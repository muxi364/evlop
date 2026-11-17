# EVLOP Self-Evolving Agent Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete `evlop` GitHub repository combining a zero-dependency Python self-evolution CLI engine (`evlop`) with universal Agent Skill/Rule protocols (`SKILL.md`, `AGENTS.md`, `CLAUDE.md`) and research documentation.

**Architecture:** Dual-layer system consisting of (1) a Python 3.10+ standard-library evolution engine (`src/evlop/`) that manages `.evlop/` workspace state, deterministic command verification, Darwinian fitness scoring, gene deduplication/pruning, and Markdown marker compilation; and (2) declarative Agent protocols, templates, and research guides (`docs/`, `templates/`, root `SKILL.md`/`AGENTS.md`/`CLAUDE.md`).

**Tech Stack:** Python 3.10+ Standard Library (`json`, `argparse`, `subprocess`, `hashlib`, `math`, `pathlib`, `datetime`, `re`, `unittest`), Git, Markdown.

**Spec:** `C:\Users\lenovo\.gemini\antigravity\scratch\evlop\docs\superpowers\specs\2026-11-18-evlop-framework-design.md`

## Global Constraints

- Runtime Dependency Constraint: Core CLI (`evlop`) must run on Python 3.10+ using standard library modules only (`json`, `argparse`, `subprocess`, `hashlib`, `math`, `pathlib`, `datetime`, `re`, `unittest`).
- Token Budget Constraint: Auto-generated rule blocks injected into `CLAUDE.md` / `AGENTS.md` must be capped at `max_active_genes = 15` (default), sorted by fitness score descending.
- Anti-Goal (No Unverified Self-Modification): A gene cannot be promoted to `"promoted"` status unless `verified_gate == True` and `success_count >= 1`.
- Default Config Values: `max_active_genes: 15`, `promote_threshold: 1.15`, `prune_threshold: 0.35`, `half_life_days: 30.0`.

## Review Focus

1. **Unverified Gene Promotion Attempt (Reward Hacking):** When `evlop log` is called without a passing `.evlop/last_verify.json` (or when `last_verify.passed == False`), `verified_gate` must remain `False` and `evlop evolve` must never promote that gene regardless of `success_count`.
2. **Corrupted or Missing Markdown Markers in `AGENTS.md` / `CLAUDE.md`:** When `evlop evolve` compiles genes into a target file that lacks `<!-- EVLOP:START -->` and `<!-- EVLOP:END -->` (or only has one marker), it must cleanly append a well-formed marker block at the end of the file without clobbering existing user content.
3. **Near-Duplicate Gene Flood:** When an agent logs multiple genes with slightly different wording for the same trigger/title (Jaccard token similarity $\ge 0.65$), `evlop evolve` must merge them into a single canonical gene and sum their `success_count` and `failure_count` rather than polluting the top-15 budget.
4. **Failing or Timed-Out Verification Command:** When `evlop verify` runs a command that exits non-zero, it must still write `.evlop/last_verify.json` with `passed: False` and return non-zero exit status cleanly without crashing on stderr encoding issues.
5. **Future/Malformed `last_used_at` Timestamps in Fitness Calculation:** If `last_used_at` is slightly in the future (clock skew) or malformed, $\Delta t$ must clamp to $\ge 0.0$ days so temporal decay $2^{-\Delta t / H}$ never exceeds $1.0$ or raises an unhandled exception.

---

### Task 1: Core Data Models, Darwinian Fitness Engine, and Persistence Store

**Files:**
- Create: `pyproject.toml`
- Create: `src/evlop/__init__.py`
- Create: `src/evlop/models.py`
- Create: `src/evlop/fitness.py`
- Create: `src/evlop/store.py`
- Test: `tests/test_core.py`

**Interfaces:**
- Consumes: Python 3.10+ standard library (`dataclasses`, `json`, `math`, `pathlib`, `datetime`, `re`, `hashlib`)
- Produces:
  - `src/evlop/models.py`:
    - `EvlopConfig(max_active_genes: int = 15, promote_threshold: float = 1.15, prune_threshold: float = 0.35, half_life_days: float = 30.0)`
    - `VerifyRecord(command: str, exit_code: int, passed: bool, timestamp: str, output_snippet: str)`
    - `Episode(episode_id: str, timestamp: str, task_summary: str, failure_symptom: str, root_cause: str, fix_applied: str, verified: bool, verify_cmd: str, gene_id: str)`
    - `Gene(id: str, title: str, category: str, trigger: str, strategy: str, anti_pattern: str, success_count: int = 1, failure_count: int = 0, verified_gate: bool = False, created_at: str = "", last_used_at: str = "", status: str = "candidate", fitness: float = 0.0)`
  - `src/evlop/fitness.py`:
    - `compute_fitness(gene: Gene, config: EvlopConfig, now: datetime | None = None) -> float`
    - `jaccard_similarity(text_a: str, text_b: str) -> float`
    - `govern_genes(genes: list[Gene], config: EvlopConfig, now: datetime | None = None) -> list[Gene]` (merges duplicates with similarity $\ge 0.65$, updates fitness, sets `status` to `"promoted"` / `"archived"` / `"candidate"`, returns sorted by `fitness` desc)
  - `src/evlop/store.py`:
    - `EvlopStore(root_dir: Path)` with methods `init_store() -> Path`, `load_config() -> EvlopConfig`, `save_verify(record: VerifyRecord) -> None`, `load_last_verify() -> VerifyRecord | None`, `append_episode(ep: Episode) -> None`, `load_episodes() -> list[Episode]`, `load_genes() -> list[Gene]`, `save_genes(genes: list[Gene]) -> None`, `recall_genes(query: str, top_k: int = 5) -> list[Gene]`

- [ ] **Step 1: Write the failing unit tests in `tests/test_core.py`**

```python
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from evlop.models import EvlopConfig, Gene, Episode, VerifyRecord
from evlop.fitness import compute_fitness, jaccard_similarity, govern_genes
from evlop.store import EvlopStore


class TestEvlopCore(unittest.TestCase):
    def test_fitness_formula_and_unverified_gate(self):
        cfg = EvlopConfig()
        now = datetime(2026, 11, 18, tzinfo=timezone.utc)
        g_verified = Gene(
            id="gene-1", title="Run pytest with PYTHONPATH", category="testing",
            trigger="ModuleNotFoundError in pytest", strategy="Use python -m pytest",
            anti_pattern="Running bare pytest", success_count=2, failure_count=0,
            verified_gate=True, created_at=now.isoformat(), last_used_at=now.isoformat()
        )
        g_unverified = Gene(
            id="gene-2", title="Unverified rule", category="testing",
            trigger="Some error", strategy="Guess fix",
            anti_pattern="None", success_count=5, failure_count=0,
            verified_gate=False, created_at=now.isoformat(), last_used_at=now.isoformat()
        )
        f_ver = compute_fitness(g_verified, cfg, now=now)
        f_unver = compute_fitness(g_unverified, cfg, now=now)
        # S=2, F=0 -> (3/4) * (1 + 0.5*ln(3)) * 1.5 * 1.0 = 0.75 * 1.5493 * 1.5 = 1.743
        self.assertAlmostEqual(f_ver, 0.75 * (1 + 0.5 * 1.0986122886681098) * 1.5, places=3)
        governed = govern_genes([g_verified, g_unverified], cfg, now=now)
        by_id = {g.id: g for g in governed}
        self.assertEqual(by_id["gene-1"].status, "promoted")
        self.assertNotEqual(by_id["gene-2"].status, "promoted")  # Review Focus #1: unverified never promoted

    def test_future_timestamp_clamped_and_decay_works(self):
        cfg = EvlopConfig(half_life_days=30.0)
        now = datetime(2026, 11, 18, tzinfo=timezone.utc)
        future = (now + timedelta(days=5)).isoformat()
        old = (now - timedelta(days=90)).isoformat()
        g_future = Gene(
            id="g-fut", title="Future rule", category="workflow",
            trigger="clock skew", strategy="clamp delta", anti_pattern="crash",
            success_count=1, failure_count=0, verified_gate=True,
            created_at=future, last_used_at=future
        )
        g_old = Gene(
            id="g-old", title="Stale rule", category="workflow",
            trigger="ancient error", strategy="old fix", anti_pattern="none",
            success_count=1, failure_count=2, verified_gate=False,
            created_at=old, last_used_at=old
        )
        f_fut = compute_fitness(g_future, cfg, now=now)
        self.assertGreater(f_fut, 1.0)  # Review Focus #5: future timestamp clamped cleanly
        governed = govern_genes([g_old], cfg, now=now)
        self.assertEqual(governed[0].status, "archived")

    def test_duplicate_gene_merge(self):
        cfg = EvlopConfig()
        now = datetime(2026, 11, 18, tzinfo=timezone.utc)
        g1 = Gene(
            id="g-1", title="Fix pytest import path error", category="testing",
            trigger="pytest ModuleNotFoundError src import path",
            strategy="Run python -m pytest", anti_pattern="bare pytest",
            success_count=1, failure_count=0, verified_gate=False,
            created_at=now.isoformat(), last_used_at=now.isoformat()
        )
        g2 = Gene(
            id="g-2", title="Fix pytest import path issue", category="testing",
            trigger="pytest ModuleNotFoundError src import path error",
            strategy="Always run python -m pytest", anti_pattern="bare pytest",
            success_count=2, failure_count=0, verified_gate=True,
            created_at=now.isoformat(), last_used_at=now.isoformat()
        )
        governed = govern_genes([g1, g2], cfg, now=now)
        self.assertEqual(len(governed), 1)  # Review Focus #3: near-duplicates merged
        self.assertEqual(governed[0].success_count, 3)
        self.assertTrue(governed[0].verified_gate)
        self.assertEqual(governed[0].status, "promoted")

    def test_store_roundtrip_and_recall(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvlopStore(Path(tmp))
            store.init_store()
            g = Gene(
                id="gene-sqlite-lock", title="SQLite WAL mode for concurrent reads",
                category="architecture", trigger="sqlite3.OperationalError database is locked",
                strategy="Enable PRAGMA journal_mode=WAL;", anti_pattern="Default rollback journal",
                success_count=3, failure_count=0, verified_gate=True, fitness=2.1, status="promoted"
            )
            store.save_genes([g])
            hits = store.recall_genes("sqlite3 database locked")
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].id, "gene-sqlite-lock")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_core.py" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'evlop'`

- [ ] **Step 3: Implement `pyproject.toml`, `src/evlop/__init__.py`, `src/evlop/models.py`, `src/evlop/fitness.py`, and `src/evlop/store.py`**

Key implementation details not fixed by signatures alone:
- In `fitness.py`, `jaccard_similarity(text_a, text_b)` tokenizes lowercased alphanumeric words (`re.findall(r"[a-z0-9_\-\u4e00-\u9fff]+", text.lower())`). Two genes merge in `govern_genes` if `jaccard_similarity(f"{g1.title} {g1.trigger}", f"{g2.title} {g2.trigger}") >= 0.65`.
- When merging two genes, keep the one with longer `strategy`, sum `success_count` and `failure_count`, logical-OR `verified_gate`, and take the max `last_used_at`.
- In `store.py`, `recall_genes(query, top_k)` scores non-archived genes by `(keyword_overlap_count * 2.0) + gene.fitness` and returns up to `top_k` matches with overlap > 0 (or top `top_k` genes by fitness if `query.strip() == ""` or `"*"`).

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python -m unittest discover -s tests -p "test_core.py" -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Initialize Git repository and commit Task 1**

```bash
git init -b main
git add pyproject.toml src/evlop/__init__.py src/evlop/models.py src/evlop/fitness.py src/evlop/store.py tests/test_core.py
git commit -m "feat(core): implement EVLOP models, Darwinian fitness engine, and persistence store"
```

---

### Task 2: Execution Verifier, Markdown/Skill Compiler, and CLI Entrypoint

**Files:**
- Create: `src/evlop/verifier.py`
- Create: `src/evlop/compiler.py`
- Create: `src/evlop/cli.py`
- Create: `src/evlop/__main__.py`
- Test: `tests/test_cli_and_compiler.py`

**Interfaces:**
- Consumes: `EvlopConfig`, `VerifyRecord`, `Episode`, `Gene`, `govern_genes`, `EvlopStore` from Task 1.
- Produces:
  - `src/evlop/verifier.py`:
    - `run_verification(command: str, cwd: Path, timeout_sec: int = 120) -> VerifyRecord`
  - `src/evlop/compiler.py`:
    - `MARKER_START = "<!-- EVLOP:START -->"`
    - `MARKER_END = "<!-- EVLOP:END -->"`
    - `render_genes_markdown(genes: list[Gene], max_genes: int = 15) -> str`
    - `inject_markdown_file(file_path: Path, genes: list[Gene], max_genes: int = 15) -> None`
    - `export_gene_to_skill(gene: Gene, skills_root: Path) -> Path` (writes `skills_root / f"auto-{gene.id}" / "SKILL.md"` with YAML frontmatter `name`, `description` and sections for Trigger, Strategy, Anti-Pattern, Fitness Metrics)
  - `src/evlop/cli.py`:
    - `main(argv: list[str] | None = None, root_dir: Path | None = None) -> int` supporting subcommands: `init`, `recall`, `verify`, `log`, `evolve`, `export-skill`, `status`

- [ ] **Step 1: Write the failing unit & integration tests in `tests/test_cli_and_compiler.py`**

```python
import json
import tempfile
import unittest
from pathlib import Path

from evlop.cli import main


class TestCliAndCompiler(unittest.TestCase):
    def test_verify_pass_and_fail_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(main(["init"], root_dir=root), 0)
            # Review Focus #4: failing command records passed=False cleanly and returns non-zero
            rc_fail = main(["verify", "python -c \"import sys; sys.exit(2)\""], root_dir=root)
            self.assertNotEqual(rc_fail, 0)
            last_v = json.loads((root / ".evlop" / "last_verify.json").read_text(encoding="utf-8"))
            self.assertFalse(last_v["passed"])

            rc_pass = main(["verify", "python -c \"print('ok')\""], root_dir=root)
            self.assertEqual(rc_pass, 0)
            last_v2 = json.loads((root / ".evlop" / "last_verify.json").read_text(encoding="utf-8"))
            self.assertTrue(last_v2["passed"])

    def test_end_to_end_evlop_loop_and_markdown_injection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Review Focus #2: file without existing markers gets clean marker block appended
            agents_md = root / "AGENTS.md"
            agents_md.write_text("# Existing Project Rules\n\nKeep code clean.\n", encoding="utf-8")

            main(["init"], root_dir=root)
            main(["verify", "python -c \"print('tests passed')\""], root_dir=root)
            for _ in range(2):
                main([
                    "log",
                    "--task", "Fix Windows encoding issue",
                    "--symptom", "UnicodeDecodeError cp936 when reading files",
                    "--root-cause", "Path.read_text called without encoding='utf-8'",
                    "--fix", "Always pass encoding='utf-8' to read_text/write_text",
                    "--category", "debugging",
                    "--trigger", "UnicodeDecodeError cp936 gbk file read_text",
                    "--strategy", "Specify encoding='utf-8' explicitly in all Path and open calls",
                    "--anti-pattern", "Relying on OS default locale encoding"
                ], root_dir=root)

            rc_evolve = main(["evolve", "--target", "AGENTS.md"], root_dir=root)
            self.assertEqual(rc_evolve, 0)
            updated = agents_md.read_text(encoding="utf-8")
            self.assertIn("# Existing Project Rules", updated)
            self.assertIn("<!-- EVLOP:START -->", updated)
            self.assertIn("Specify encoding='utf-8' explicitly", updated)

            genes = json.loads((root / ".evlop" / "genes.json").read_text(encoding="utf-8"))
            gene_id = genes[0]["id"]
            rc_skill = main(["export-skill", "--gene-id", gene_id, "--out-dir", "skills"], root_dir=root)
            self.assertEqual(rc_skill, 0)
            skill_file = root / "skills" / f"auto-{gene_id}" / "SKILL.md"
            self.assertTrue(skill_file.exists())
            self.assertIn("name: auto-", skill_file.read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python -m unittest discover -s tests -p "test_cli_and_compiler.py" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'evlop.cli'`

- [ ] **Step 3: Implement `src/evlop/verifier.py`, `src/evlop/compiler.py`, `src/evlop/cli.py`, and `src/evlop/__main__.py`**

Key implementation details:
- `verifier.py`: Runs `subprocess.run(command, shell=True, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout_sec)` so Windows output never triggers `UnicodeDecodeError`.
- `compiler.py`: If both `MARKER_START` and `MARKER_END` exist in `file_path` (with `start < end`), replace the slice between them; otherwise append `\n\n` + rendered block at the end of the file.
- `cli.py` `log`: Checks `store.load_last_verify()`; sets `verified = bool(last_verify and last_verify.passed)`. Generates gene slug ID from `--title` (or `--fix` if `--title` omitted), appends `Episode`, creates or updates matching `Gene`, runs `govern_genes`, and saves.

- [ ] **Step 4: Run all tests to verify they pass**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`
Expected: PASS (all tests in `test_core.py` and `test_cli_and_compiler.py`)

- [ ] **Step 5: Commit Task 2**

```bash
git add src/evlop/verifier.py src/evlop/compiler.py src/evlop/cli.py src/evlop/__main__.py tests/test_cli_and_compiler.py
git commit -m "feat(cli): implement verification gate, markdown/skill compiler, and CLI entrypoint"
```

---

### Task 3: Agent Protocol Files (`SKILL.md`, `AGENTS.md`, `CLAUDE.md`) and Reusable Templates

**Files:**
- Create: `SKILL.md`
- Create: `AGENTS.md`
- Create: `CLAUDE.md`
- Create: `templates/CLAUDE.template.md`
- Create: `templates/AGENTS.template.md`
- Create: `templates/claude-settings-hooks.json`
- Test: `tests/test_protocols.py`

**Interfaces:**
- Consumes: `evlop.cli.main` from Task 2.
- Produces:
  - Root `SKILL.md` with valid YAML frontmatter (`name: evlop`, `description: ...`) teaching any Agent how to execute the 5-stage **E-V-L-O-P** self-evolution loop.
  - Root `AGENTS.md` and `CLAUDE.md` pre-populated with EVLOP operational rules and live `<!-- EVLOP:START -->...<!-- EVLOP:END -->` blocks seeded via `evlop`.
  - `templates/` directory for one-command adoption in external repositories.

- [ ] **Step 1: Write the failing protocol validation test in `tests/test_protocols.py`**

```python
import json
import unittest
from pathlib import Path


class TestProtocolsAndTemplates(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent

    def test_skill_md_has_frontmatter_and_five_stages(self):
        skill_text = (self.repo_root / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill_text.startswith("---\n"))
        for keyword in ["name: evlop", "evlop recall", "evlop verify", "evlop log", "evlop evolve", "evlop export-skill"]:
            self.assertIn(keyword, skill_text)

    def test_agents_and_claude_md_contain_evlop_markers(self):
        for fname in ["AGENTS.md", "CLAUDE.md", "templates/AGENTS.template.md", "templates/CLAUDE.template.md"]:
            content = (self.repo_root / fname).read_text(encoding="utf-8")
            self.assertIn("<!-- EVLOP:START -->", content)
            self.assertIn("<!-- EVLOP:END -->", content)

    def test_claude_hooks_template_is_valid_json(self):
        hooks_path = self.repo_root / "templates" / "claude-settings-hooks.json"
        data = json.loads(hooks_path.read_text(encoding="utf-8"))
        self.assertIn("hooks", data)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python -m unittest discover -s tests -p "test_protocols.py" -v`
Expected: FAIL with `FileNotFoundError`

- [ ] **Step 3: Create `SKILL.md`, `AGENTS.md`, `CLAUDE.md`, and `templates/*`, and seed initial `.evlop/` genome**

Seed `.evlop/` with 3 foundational self-evolution genes distilled from Claude's engineering practices (1. Execution-Verified Patching, 2. Subagent Context Isolation for Exploration, 3. UTF-8 Explicit I/O & Minimal Diff Discipline) and compile them into `AGENTS.md` and `CLAUDE.md`.

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python -m unittest discover -s tests -p "test_protocols.py" -v`
Expected: PASS

- [ ] **Step 5: Commit Task 3**

```bash
git add SKILL.md AGENTS.md CLAUDE.md templates/ .evlop/ tests/test_protocols.py
git commit -m "feat(protocol): add SKILL.md, AGENTS.md, CLAUDE.md, hooks templates, and seed genome"
```

---

### Task 4: Comprehensive Documentation, Academic Paper & Ecosystem Hub, and GitHub Repo Packaging

**Files:**
- Create: `README.md`
- Create: `README_EN.md`
- Create: `LICENSE`
- Create: `docs/why-claude-is-strong.md`
- Create: `docs/evlop-methodology.md`
- Create: `docs/papers-and-ecosystem.md`
- Create: `.gitignore`
- Test: `tests/test_docs_completeness.py`

**Interfaces:**
- Consumes: All artifacts from Tasks 1–3 and the Spec (`docs/superpowers/specs/2026-11-18-evlop-framework-design.md`).
- Produces: Complete, publication-grade bilingual GitHub repository with all academic citations, architecture diagrams, CLI reference, and clean Git commit history.

- [ ] **Step 1: Write the failing documentation completeness test in `tests/test_docs_completeness.py`**

```python
import unittest
from pathlib import Path


class TestDocsCompleteness(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent

    def test_required_docs_and_citations_exist(self):
        required_files = [
            "README.md",
            "README_EN.md",
            "LICENSE",
            ".gitignore",
            "docs/why-claude-is-strong.md",
            "docs/evlop-methodology.md",
            "docs/papers-and-ecosystem.md",
        ]
        for rel in required_files:
            self.assertTrue((self.root / rel).exists(), f"Missing {rel}")

        papers_doc = (self.root / "docs/papers-and-ecosystem.md").read_text(encoding="utf-8")
        for citation in [
            "2507.21046",  # Gao et al. TMLR 2026 Survey
            "2508.07407",  # Fang et al. Survey
            "2607.13104",  # Ren et al. 2026 Survey
            "Reflexion",
            "Voyager",
            "TextGrad",
            "ADAS",
            "SWE-agent",
            "Dive-into-Claude-Code",
            "claude-evolve",
            "Self-Evolving-Skill",
        ]:
            self.assertIn(citation, papers_doc)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python -m unittest discover -s tests -p "test_docs_completeness.py" -v`
Expected: FAIL

- [ ] **Step 3: Create `README.md`, `README_EN.md`, `LICENSE`, `.gitignore`, and `docs/*.md`**

Ensure `README.md` includes:
1. Executive overview of EVLOP & why Claude 5.2/5.5 is so strong.
2. Mermaid architecture diagram of the E-V-L-O-P 5-stage self-evolution loop.
3. Quickstart for any AI Agent (Claude Code, Antigravity, Cursor, OpenHands) and CLI commands.
4. Summary table of academic papers (`arXiv:2507.21046`, `arXiv:2508.07407`, `arXiv:2607.13104`, Reflexion, Voyager, TextGrad, ADAS, SWE-agent) and open-source projects, linking to `docs/papers-and-ecosystem.md`, `docs/why-claude-is-strong.md`, and `docs/evlop-methodology.md`.

- [ ] **Step 4: Run full test suite to verify everything passes**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`
Expected: PASS (all tests across all 4 test files pass with 0 errors)

- [ ] **Step 5: Commit Task 4 and verify clean git status**

```bash
git add README.md README_EN.md LICENSE .gitignore docs/ tests/test_docs_completeness.py
git commit -m "docs: add bilingual READMEs, Claude architecture analysis, and self-evolving agent literature hub"
git status
```
