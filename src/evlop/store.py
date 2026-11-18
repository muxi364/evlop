"""Workspace persistence store (.evlop/) with cross-process/thread locking, TTL validation, and recall."""

from __future__ import annotations

from contextlib import contextmanager
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
        self.episodes_file = self.evlop_dir / "episodes.jsonl"
        self.genes_file = self.evlop_dir / "genes.json"
        self.lock_file = self.evlop_dir / ".lock"

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
                    # Break stale lock if older than 30 seconds
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

    def save_verify(self, record: VerifyRecord) -> None:
        _atomic_write_text(
            self.verify_file,
            json.dumps(record.to_dict(), indent=2, ensure_ascii=False) + "\n",
        )

    def load_last_verify(self) -> VerifyRecord | None:
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

    def save_failure(self, diag: FailureDiagnosis) -> None:
        _atomic_write_text(
            self.failure_file,
            json.dumps(diag.to_dict(), indent=2, ensure_ascii=False) + "\n",
        )

    def load_last_failure(self) -> FailureDiagnosis | None:
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

    def recall_genes(self, query: str, top_k: int = 5) -> list[Gene]:
        """Search active (non-archived, non-superseded) genes by BM25-style Corpus IDF, field weighting, and fitness."""
        active = [g for g in self.load_genes() if g.status not in ("archived", "superseded")]
        if not active:
            return []

        q_clean = query.strip()
        if not q_clean or q_clean == "*":
            active.sort(key=lambda g: g.fitness, reverse=True)
            return active[:top_k]

        q_tokens = tokenize(q_clean)
        n_docs = len(active)

        gene_fields: list[tuple[Gene, set[str], set[str], set[str], set[str]]] = []
        df_counts: dict[str, int] = {t: 0 for t in q_tokens}

        for g in active:
            high_tokens = tokenize(f"{g.id} {g.title} {g.trigger}")
            med_tokens = tokenize(f"{g.category} {g.strategy}")
            anti_tokens = tokenize(g.anti_pattern)
            all_doc_tokens = high_tokens | med_tokens | anti_tokens
            gene_fields.append((g, high_tokens, med_tokens, anti_tokens, all_doc_tokens))
            for t in q_tokens:
                if t in all_doc_tokens:
                    df_counts[t] += 1

        idf: dict[str, float] = {
            t: math.log(1.0 + (max(0.0, n_docs - df) + 0.5) / (df + 0.5))
            for t, df in df_counts.items()
        }

        scored: list[tuple[float, Gene]] = []
        q_lower = q_clean.lower()
        for g, high_tokens, med_tokens, anti_tokens, all_doc_tokens in gene_fields:
            matched_tokens = q_tokens & all_doc_tokens
            lexical_score = 0.0
            for t in matched_tokens:
                field_w = 0.0
                if t in high_tokens:
                    field_w += 3.0
                if t in med_tokens:
                    field_w += 1.5
                if t not in high_tokens and t not in med_tokens and t in anti_tokens:
                    field_w += 1.0
                lexical_score += idf[t] * field_w

            if lexical_score > 0.0 or q_lower in f"{g.title} {g.trigger} {g.strategy}".lower():
                effective_lexical = max(1.0, lexical_score)
                score = (effective_lexical * 2.0) + g.fitness
                scored.append((score, g))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [g for _, g in scored[:top_k]]
