"""Workspace persistence store (.evlop/) with cross-process locking, TTL check, and Mtime-Cached Inverted Index."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import threading
import time
from typing import Iterator
import uuid

from evlop.fitness import tokenize
from evlop.models import Episode, EvlopConfig, FailureDiagnosis, Gene, VerifyRecord

_IN_PROCESS_LOCK = threading.RLock()


@dataclass
class _CompiledSearchIndex:
    active_genes: list[Gene]
    sorted_by_fitness: list[Gene]
    postings: dict[str, list[tuple[int, float]]]
    concat_lower: list[str]


_SEARCH_INDEX_CACHE: dict[Path, tuple[int, int, float, _CompiledSearchIndex]] = {}


def _build_compiled_index(genes: list[Gene]) -> _CompiledSearchIndex:
    active = [g for g in genes if g.status not in ("archived", "superseded")]
    sorted_by_fitness = sorted(active, key=lambda g: g.fitness, reverse=True)
    n_docs = len(active)
    if not active:
        return _CompiledSearchIndex([], [], {}, [])

    doc_token_weights: list[dict[str, float]] = []
    df_counts: dict[str, int] = {}
    concat_lower: list[str] = []

    for g in active:
        high_tokens = tokenize(f"{g.id} {g.title} {g.trigger}")
        med_tokens = tokenize(f"{g.category} {g.strategy}")
        anti_tokens = tokenize(g.anti_pattern)
        all_tokens = high_tokens | med_tokens | anti_tokens

        weights: dict[str, float] = {}
        for t in all_tokens:
            w = 0.0
            if t in high_tokens:
                w += 3.0
            if t in med_tokens:
                w += 1.5
            if t not in high_tokens and t not in med_tokens and t in anti_tokens:
                w += 1.0
            weights[t] = w
            df_counts[t] = df_counts.get(t, 0) + 1

        doc_token_weights.append(weights)
        concat_lower.append(f"{g.title} {g.trigger} {g.strategy}".lower())

    postings: dict[str, list[tuple[int, float]]] = {}
    for doc_idx, weights in enumerate(doc_token_weights):
        for t, field_w in weights.items():
            df = df_counts[t]
            idf = math.log(1.0 + (max(0.0, n_docs - df) + 0.5) / (df + 0.5))
            postings.setdefault(t, []).append((doc_idx, idf * field_w))

    return _CompiledSearchIndex(
        active_genes=active,
        sorted_by_fitness=sorted_by_fitness,
        postings=postings,
        concat_lower=concat_lower,
    )


def _atomic_write_text(target: Path, content: str) -> None:
    """Write text atomically via a sibling temporary file and os.replace with Windows retry."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.parent / f".{target.name}.{uuid.uuid4().hex[:8]}.tmp"
    try:
        tmp_path.write_text(content, encoding="utf-8")
        for attempt in range(15):
            try:
                os.replace(str(tmp_path), str(target))
                break
            except PermissionError:
                if attempt == 14:
                    raise
                time.sleep(0.01 * (attempt + 1))
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


class EvlopStore:
    """Manages .evlop/ directory state inside a project workspace with swarm concurrency safety."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = Path(root_dir).resolve()
        self.evlop_dir = self.root_dir / ".evlop"
        self.config_file = self.evlop_dir / "config.json"
        self.verify_file = self.evlop_dir / "last_verify.json"
        self.failure_file = self.evlop_dir / "last_failure.json"
        self.verify_state_dir = self.evlop_dir / "verify_state"
        self.episodes_file = self.evlop_dir / "episodes.jsonl"
        self.genes_file = self.evlop_dir / "genes.json"
        self.lock_file = self.evlop_dir / ".lock"

    def _agent_verify_file(self, agent_id: str) -> Path:
        safe_id = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in agent_id.strip())
        return self.verify_state_dir / f"last_verify_{safe_id}.json"

    def _agent_failure_file(self, agent_id: str) -> Path:
        safe_id = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in agent_id.strip())
        return self.verify_state_dir / f"last_failure_{safe_id}.json"

    @contextmanager
    def lock(self, timeout_sec: float = 10.0) -> Iterator[None]:
        """Acquire both in-process RLock and cross-process exclusive file lock (.evlop/.lock)."""
        self.evlop_dir.mkdir(parents=True, exist_ok=True)
        with _IN_PROCESS_LOCK:
            deadline = time.monotonic() + timeout_sec
            fd: int | None = None
            while True:
                try:
                    fd = os.open(str(self.lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                    break
                except FileExistsError:
                    try:
                        if time.time() - self.lock_file.stat().st_mtime > 30.0:
                            self.lock_file.unlink()
                            continue
                    except OSError:
                        pass
                    if time.monotonic() >= deadline:
                        break
                    time.sleep(0.01)
            try:
                yield
            finally:
                if fd is not None:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                    try:
                        self.lock_file.unlink()
                    except OSError:
                        pass

    def init_store(self) -> Path:
        """Create .evlop/ directory and default files if they do not exist."""
        with self.lock():
            self.evlop_dir.mkdir(parents=True, exist_ok=True)
            if not self.config_file.exists():
                self.save_config(EvlopConfig())
            if not self.genes_file.exists():
                self.save_genes([])
            if not self.episodes_file.exists():
                self.episodes_file.write_text("", encoding="utf-8")
        return self.evlop_dir

    def load_config(self) -> EvlopConfig:
        if not self.config_file.exists():
            return EvlopConfig()
        data = json.loads(self.config_file.read_text(encoding="utf-8"))
        return EvlopConfig.from_dict(data)

    def save_config(self, config: EvlopConfig) -> None:
        _atomic_write_text(
            self.config_file,
            json.dumps(config.to_dict(), indent=2, ensure_ascii=False) + "\n",
        )

    def save_verify(self, record: VerifyRecord, agent_id: str = "") -> None:
        payload_txt = json.dumps(record.to_dict(), indent=2, ensure_ascii=False) + "\n"
        _atomic_write_text(self.verify_file, payload_txt)
        if agent_id and agent_id != "default-agent":
            _atomic_write_text(self._agent_verify_file(agent_id), payload_txt)

    def load_last_verify(self, agent_id: str = "") -> VerifyRecord | None:
        if agent_id and agent_id != "default-agent":
            agent_vf = self._agent_verify_file(agent_id)
            if agent_vf.exists():
                data = json.loads(agent_vf.read_text(encoding="utf-8"))
                return VerifyRecord.from_dict(data)
        if not self.verify_file.exists():
            return None
        data = json.loads(self.verify_file.read_text(encoding="utf-8"))
        return VerifyRecord.from_dict(data)

    def is_verify_fresh(self, record: VerifyRecord | None, ttl_minutes: float = 30.0) -> bool:
        """Return True only if `record` passed and was recorded within `ttl_minutes`."""
        if not record or not record.passed or not record.timestamp:
            return False
        try:
            ts_str = record.timestamp[:-1] + "+00:00" if record.timestamp.endswith("Z") else record.timestamp
            parsed = datetime.fromisoformat(ts_str)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            elapsed_min = (datetime.now(timezone.utc) - parsed).total_seconds() / 60.0
            return elapsed_min <= ttl_minutes
        except (ValueError, TypeError):
            return False

    def save_failure(self, diag: FailureDiagnosis, agent_id: str = "") -> None:
        payload_txt = json.dumps(diag.to_dict(), indent=2, ensure_ascii=False) + "\n"
        _atomic_write_text(self.failure_file, payload_txt)
        if agent_id and agent_id != "default-agent":
            _atomic_write_text(self._agent_failure_file(agent_id), payload_txt)

    def load_last_failure(self, agent_id: str = "") -> FailureDiagnosis | None:
        if agent_id and agent_id != "default-agent":
            agent_ff = self._agent_failure_file(agent_id)
            if agent_ff.exists():
                data = json.loads(agent_ff.read_text(encoding="utf-8"))
                return FailureDiagnosis.from_dict(data)
        if not self.failure_file.exists():
            return None
        data = json.loads(self.failure_file.read_text(encoding="utf-8"))
        return FailureDiagnosis.from_dict(data)

    def append_episode(self, ep: Episode) -> None:
        self.evlop_dir.mkdir(parents=True, exist_ok=True)
        line = json.dumps(ep.to_dict(), ensure_ascii=False)
        with self.episodes_file.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def load_episodes(self) -> list[Episode]:
        if not self.episodes_file.exists():
            return []
        episodes: list[Episode] = []
        for line in self.episodes_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                episodes.append(Episode.from_dict(json.loads(stripped)))
        return episodes

    def load_genes(self) -> list[Gene]:
        if not self.genes_file.exists():
            return []
        raw = json.loads(self.genes_file.read_text(encoding="utf-8"))
        return [Gene.from_dict(item) for item in raw]

    def save_genes(self, genes: list[Gene]) -> None:
        payload = [g.to_dict() for g in genes]
        _atomic_write_text(
            self.genes_file,
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        )
        try:
            st = self.genes_file.stat()
            _SEARCH_INDEX_CACHE[self.genes_file] = (
                st.st_mtime_ns,
                st.st_size,
                time.monotonic(),
                _build_compiled_index(genes),
            )
        except OSError:
            pass

    def _get_search_index(self) -> _CompiledSearchIndex:
        now_mono = time.monotonic()
        cached = _SEARCH_INDEX_CACHE.get(self.genes_file)
        if cached and (now_mono - cached[2]) < 0.05:
            return cached[3]
        try:
            st = self.genes_file.stat()
            if cached and cached[0] == st.st_mtime_ns and cached[1] == st.st_size:
                _SEARCH_INDEX_CACHE[self.genes_file] = (cached[0], cached[1], now_mono, cached[3])
                return cached[3]
            genes = self.load_genes()
            compiled = _build_compiled_index(genes)
            _SEARCH_INDEX_CACHE[self.genes_file] = (st.st_mtime_ns, st.st_size, now_mono, compiled)
            return compiled
        except FileNotFoundError:
            return _CompiledSearchIndex([], [], {}, [])
        except OSError:
            return _build_compiled_index(self.load_genes())

    def recall_genes(self, query: str, top_k: int = 5) -> list[Gene]:
        """Search active genes in sub-millisecond time using Mtime-Cached Weighted Inverted Index."""
        idx = self._get_search_index()
        if not idx.active_genes:
            return []

        q_clean = query.strip()
        if not q_clean or q_clean == "*":
            return idx.sorted_by_fitness[:top_k]

        q_tokens = tokenize(q_clean)
        lexical_scores: dict[int, float] = {}
        for t in q_tokens:
            for doc_idx, weight in idx.postings.get(t, ()):
                lexical_scores[doc_idx] = lexical_scores.get(doc_idx, 0.0) + weight

        q_lower = q_clean.lower()
        if not lexical_scores:
            for doc_idx, text_lower in enumerate(idx.concat_lower):
                if q_lower in text_lower:
                    lexical_scores[doc_idx] = 1.0

        if not lexical_scores:
            return []

        scored: list[tuple[float, Gene]] = []
        for doc_idx, lex in lexical_scores.items():
            g = idx.active_genes[doc_idx]
            score = (max(1.0, lex) * 2.0) + g.fitness
            scored.append((score, g))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [g for _, g in scored[:top_k]]
