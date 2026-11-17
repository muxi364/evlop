"""Workspace persistence store (.evlop/) and keyword+fitness gene recall."""

from __future__ import annotations

import json
from pathlib import Path

from evlop.fitness import tokenize
from evlop.models import Episode, EvlopConfig, Gene, VerifyRecord


class EvlopStore:
    """Manages .evlop/ directory state inside a project workspace."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = Path(root_dir).resolve()
        self.evlop_dir = self.root_dir / ".evlop"
        self.config_file = self.evlop_dir / "config.json"
        self.verify_file = self.evlop_dir / "last_verify.json"
        self.episodes_file = self.evlop_dir / "episodes.jsonl"
        self.genes_file = self.evlop_dir / "genes.json"

    def init_store(self) -> Path:
        """Create .evlop/ directory and default files if they do not exist."""
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
        self.evlop_dir.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(
            json.dumps(config.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def save_verify(self, record: VerifyRecord) -> None:
        self.evlop_dir.mkdir(parents=True, exist_ok=True)
        self.verify_file.write_text(
            json.dumps(record.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def load_last_verify(self) -> VerifyRecord | None:
        if not self.verify_file.exists():
            return None
        data = json.loads(self.verify_file.read_text(encoding="utf-8"))
        return VerifyRecord.from_dict(data)

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
        self.evlop_dir.mkdir(parents=True, exist_ok=True)
        payload = [g.to_dict() for g in genes]
        self.genes_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def recall_genes(self, query: str, top_k: int = 5) -> list[Gene]:
        """Search active (non-archived) genes by keyword overlap + Darwinian fitness."""
        active = [g for g in self.load_genes() if g.status != "archived"]
        if not active:
            return []

        q_clean = query.strip()
        if not q_clean or q_clean == "*":
            active.sort(key=lambda g: g.fitness, reverse=True)
            return active[:top_k]

        q_tokens = tokenize(q_clean)
        scored: list[tuple[float, Gene]] = []
        for g in active:
            doc_tokens = tokenize(f"{g.id} {g.title} {g.category} {g.trigger} {g.strategy}")
            overlap = len(q_tokens & doc_tokens)
            if overlap > 0 or q_clean.lower() in f"{g.title} {g.trigger} {g.strategy}".lower():
                effective_overlap = max(1, overlap)
                score = (effective_overlap * 2.0) + g.fitness
                scored.append((score, g))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [g for _, g in scored[:top_k]]
