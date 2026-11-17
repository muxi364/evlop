# EVLOP: Self-Evolving Agent Framework — Design Specification

- **Date:** 2026-11-18
- **Status:** Draft (Pending User Approval)
- **Target Repository Path:** `C:\Users\lenovo\.gemini\antigravity\scratch\evlop`
- **Target GitHub Account:** `muxi364` (via `gh repo create` once authenticated, or local Git repository ready for remote push)

---

## 1. Intent & The Why

Modern AI coding agents (Claude Code, Antigravity, Cursor, Codex, OpenHands, SWE-agent) achieve remarkable single-session performance—especially Anthropic's Claude 5.5 / Fable 5.2 lineage—because of tight coupling between **execution-guided feedback loops**, **specialized tool harnesses**, and **strict context governance**.

However, most agents suffer from **cross-session amnesia**:
1. Mistakes debugged at high token cost in Session $N$ are repeated in Session $N+1$.
2. Naive "append-only" memory files (`MEMORY.md` or bloated `CLAUDE.md` files) quickly suffer from **Context Rot**—growing noisy, contradictory, and degrading attention precision.
3. Existing agents lack a standardized, host-agnostic mechanism to turn transient runtime trajectories (errors, fixes, verification commands) into permanent, fitness-scored rules and reusable skills.

**EVLOP** distills the core architectural secrets behind Claude's dominance—combined with the latest 2023–2026 academic research and top open-source self-evolving agent projects—into a **universal, lightweight Self-Evolution Framework** that **any AI Agent** can mount as a Skill/Protocol and invoke via a zero-dependency CLI engine to achieve lifelong self-improvement.

---

## 2. Theoretical Foundation & Open-Source Synthesis

*(Author's Call — synthesizing user request to combine top open-source solutions, latest papers, and related projects)*

EVLOP bridges five foundational paradigms from academic literature and open-source engineering into its five-stage lifecycle:

| EVLOP Stage | Core Mechanism | Academic Papers (arXiv / Venue) | Reference Open-Source Projects |
| :--- | :--- | :--- | :--- |
| **E — Execute & Explore** | Grounded sandbox action & Agent-Computer Interface (ACI) trajectory capture | • **SWE-agent** (*Yang et al., NeurIPS 2024*, `arXiv:2405.15793`)<br>• **Survey of Self-Evolving Agents** (*Gao et al., TMLR 2026*, `arXiv:2507.21046`) | • `anthropics/claude-code`<br>• `VILA-Lab/Dive-into-Claude-Code` (TAOR Loop)<br>• `CharlesQ9/Self-Evolving-Agents` |
| **V — Verify & Validate** | Deterministic execution gate (tests, exit codes, assertions) preventing hallucinated success | • **Comprehensive Survey of Self-Evolving AI Agents** (*Fang et al., 2025*, `arXiv:2508.07407`) | • `mickeyyaya/evolve-loop`<br>• `evanklem/evanflow` |
| **L — Learn & Log** | Verbal reinforcement learning & textual gradient extraction from `(failure -> fix)` diffs | • **Reflexion** (*Shinn et al., NeurIPS 2023*, `arXiv:2303.11366`)<br>• **TextGrad** (*Yuksekgonul et al., Nature 2025*, `arXiv:2406.07496`) | • `EvoMap/evolver-claude-code-mods` (Genome Evolution Protocol)<br>• `coleam00/claude-memory-compiler` |
| **O — Orchestrate & Optimize** | Subagent context isolation, progressive disclosure, and Darwinian fitness scoring / pruning | • **Self-Improvements in Modern Agentic Systems** (*Ren et al., 2026*, `arXiv:2607.13104`) | • `ethanbytes/Self-Evolving-Skill` (MUSE/Mem0 4-layer memory ops: add/merge/update/delete)<br>• `jack60810/claude-evolve` |
| **P — Persist & Promote** | Promoting high-fitness genes into permanent Agent Rules (`CLAUDE.md`/`AGENTS.md`) & executable Skills (`SKILL.md`) | • **Voyager** (*Wang et al., 2023*, `arXiv:2305.16291`)<br>• **ADAS** (*Hu et al., ICLR 2025*, `arXiv:2408.08435`) | • `Piebald-AI/claude-code-system-prompts`<br>• `XMUDeepLIT/Awesome-Self-Evolving-Agents`<br>• `ANative-Lab/Awesome-Self-Evolving-Agents` |

---

## 3. Goals, Non-Goals, and Anti-Goals

### Goals
1. **Host-Agent Agnostic:** Usable out-of-the-box by Claude Code, Antigravity, Cursor, Windsurf, Codex, OpenHands, or custom agents via standard markdown protocols (`SKILL.md`, `AGENTS.md`, `CLAUDE.md`) plus a standard Python CLI (`evlop`).
2. **Deterministic Evolution Engine:** Provide a working, tested Python package (`src/evlop`) using **only the Python 3.10+ standard library** (zero external `pip` dependencies required at runtime) so it executes reliably inside restricted agent sandboxes.
3. **Darwinian Memory Governance (Anti-Context-Rot):** Track structured experiences (**Episodes**) and distilled reusable rules (**Genes**) with a formal **Fitness Score** formula that rewards verified reuse and decays stale rules, automatically promoting top genes into `AGENTS.md`/`CLAUDE.md`/`SKILL.md` and archiving low-fitness ones.
4. **Comprehensive Research & Ecosystem Hub:** Include a curated documentation suite mapping Claude's internal harness patterns, the EVLOP mathematical/system specification, and a full bibliography of self-evolving agent papers and GitHub projects.

### Non-Goals
1. **Not a Standalone LLM Wrapper:** EVLOP does not make paid API calls to OpenAI/Anthropic itself or replace the host agent's main LLM loop; the **host agent** supplies the intelligence while EVLOP provides the protocol, memory store, verification harness, and fitness compiler.
2. **Not a Heavy Vector Database:** EVLOP uses human-readable, Git-friendly JSONL/JSON and Markdown files (`.evlop/`) with built-in BM25/keyword + tag retrieval rather than requiring Dockerized Postgres/Milvus/Chroma instances.

### Anti-Goals (What Would Make This a Failure Even If It Works)
1. **Context Bloat / Prompt Pollution:** Dumping raw historical logs into `CLAUDE.md` or `AGENTS.md` without fitness filtering and token-budget caps.
2. **Unverified Self-Modification (Reward Hacking):** Allowing an agent to promote a "lesson learned" into permanent rules when the underlying verification command (`evlop verify`) actually failed.

---

## 4. Constraints

- **Runtime Dependency Constraint:** Core CLI (`evlop`) must run on Python 3.10+ using standard library modules only (`json`, `argparse`, `subprocess`, `hashlib`, `math`, `pathlib`, `datetime`, `re`, `unittest`) so any agent can run it immediately without environment setup failures.
- **Token Budget Constraint:** Any auto-generated rule block injected into `CLAUDE.md` / `AGENTS.md` must be strictly capped (default max 15 active promoted genes, sorted by fitness score) using progressive disclosure (pointing to `.evlop/skills/` for deep details).
- **Bilingual Documentation:** Primary README and specs should clearly serve Chinese developers (matching user preference) while providing clean English technical identifiers and an English `README_EN.md` for global GitHub reach *(Builder's Call)*.

---

## 5. Approaches Considered

### Approach A (Selected): Dual-Layer Architecture — Declarative Agent Protocol + Zero-Dependency Python Evolution Engine
- **Description:** Combines (1) universal agent protocol files (`SKILL.md`, `CLAUDE.md`, `AGENTS.md` templates) that instruct any host agent *when and how* to trigger the EVLOP loop, with (2) an executable Python CLI tool (`evlop`) that manages `.evlop/` storage, runs verification shell commands, calculates Darwinian fitness scores, performs `add/merge/update/prune` governance, and compiles top genes into `CLAUDE.md` / `AGENTS.md` and `SKILL.md`.
- **Trade-offs:** Slightly more initial code to build than a pure-Markdown repo, but eliminates agent hallucination during memory management and gives developers a real, testable tool.
- **Why Selected:** Chosen by user + recommended because it mirrors Anthropic's core insight (*Model Cognition + Deterministic Harness Co-design*) and synthesizes top open-source implementations (`jack60810/claude-evolve`, `EvoMap/evolver-claude-code-mods`, `ethanbytes/Self-Evolving-Skill`).

### Approach B: Pure Declarative Markdown & Prompt Templates
- **Description:** Only Markdown prompts and manual checklists; the host agent edits `.evlop/` and `CLAUDE.md` directly with file-edit tools.
- **Trade-offs:** Zero code, but no deterministic verification gate, no mathematical fitness decay, and high risk of malformed JSON or unbounded prompt bloat.

### Approach C: Monolithic Agent Runtime SDK
- **Description:** A full Python agent framework that wraps Anthropic/OpenAI SDKs directly.
- **Trade-offs:** Cannot be used natively inside existing coding agents like Claude Code, Antigravity, or Cursor without external API keys and separate processes.

---

## 6. Detailed System Architecture (Decided & Proposed)

### 6.1 The EVLOP Five-Stage Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        HOST AGENT (Claude / AGY / etc.)                 │
└───────┬────────────────┬────────────────┬───────────────┬───────────────┘
        │ 1. Explore     │ 2. Verify      │ 3. Log/Learn  │ 4. Optimize &
        ▼                ▼                ▼               ▼    5. Promote
┌───────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────────────┐
│  [E] Execute  │→│  [V] Verify  │→│  [L] Learn   │→│ [O] Orchestrate &   │
│  & Explore    │ │  & Validate  │ │  & Log       │ │ [P] Persist/Promote │
├───────────────┤ ├──────────────┤ ├──────────────┤ ├─────────────────────┤
│ • Read Genes  │ │ • Run Test   │ │ • Record     │ │ • Merge duplicates  │
│ • Subagent    │ │   Gate via   │ │   Episode    │ │ • Compute Darwinian │
│   Isolation   │ │   `evlop     │ │ • Extract    │ │   Fitness Score     │
│ • Edit Code   │ │   verify`    │ │   Gene (Rule │ │ • Prune stale genes │
│               │ │ • Capture    │ │   + Trigger  │ │ • Compile top genes │
│               │ │   Exit Code  │ │   + Action)  │ │   to AGENTS.md &    │
│               │ │   & Output   │ │              │ │   SKILL.md          │
└───────────────┘ └──────────────┘ └──────────────┘ └─────────────────────┘
```

### 6.2 Data Model (`.evlop/` Workspace Directory)

When initialized in any project (`evlop init`), EVLOP maintains:
1. `.evlop/config.json`: Thresholds (`max_active_genes`: 15, `promote_threshold`: 1.5, `prune_threshold`: 0.25, `half_life_days`: 30).
2. `.evlop/last_verify.json`: Deterministic proof of the last `evlop verify "<cmd>"` run (command, exit_code, timestamp, stdout/stderr digest, pass/fail boolean).
3. `.evlop/episodes.jsonl`: Append-only execution trace log:
   - `episode_id`, `timestamp`, `task_summary`, `failure_symptom`, `root_cause`, `fix_applied`, `verified` (bool), `verify_cmd`, `gene_id` (if a gene was created/reinforced).
4. `.evlop/genes.json`: The structured genome of reusable evolutionary rules:
   - `id`: Deterministic hash or slug (e.g., `gene-pytest-import-path`)
   - `title`: Short imperative rule title
   - `category`: `"debugging" | "architecture" | "testing" | "tooling" | "workflow"`
   - `trigger`: When the agent should activate this gene (symptom / file pattern / error type)
   - `strategy`: Concrete actionable instruction or command sequence
   - `anti_pattern`: What *not* to do (captured from prior failure)
   - `success_count`: Integer count of verified successes using this gene
   - `failure_count`: Integer count of failures when this gene was applied
   - `verified_gate`: Boolean (true if backed by a passing `evlop verify` run)
   - `created_at` / `last_used_at`: ISO-8601 timestamps
   - `status`: `"candidate" | "promoted" | "archived"`
   - `fitness`: Float computed by the Darwinian Fitness Formula

### 6.3 Darwinian Fitness Formula *(Builder's Call)*

To balance empirical reliability, verification rigor, and recency (inspired by `jack60810/claude-evolve` and `EvoMap` GEP):

$$\text{Fitness}(g) = \underbrace{\frac{S + 1}{S + F + 2}}_{\text{Laplace Smoothed Success Rate}} \times \underbrace{\left(1 + 0.5 \cdot \ln(1 + S)\right)}_{\text{Experience Volume Boost}} \times \underbrace{V_{\text{bonus}}}_{\text{Verification Multiplier}} \times \underbrace{2^{-\Delta t / H}}_{\text{Temporal Decay}}$$

Where:
- $S = \text{success\_count}$, $F = \text{failure\_count}$
- $V_{\text{bonus}} = 1.5$ if `verified_gate == True` else $0.8$ (penalizes unverified claims)
- $\Delta t$ = days since `last_used_at`, $H$ = `half_life_days` (default `30.0`)

**Governance Operations (`evlop evolve`):**
- **Merge:** Genes with overlapping triggers/titles (Jaccard token similarity $\ge 0.65$) are automatically merged, summing their $S$ and $F$ counts.
- **Promote:** Genes with $\text{Fitness}(g) \ge \text{promote\_threshold}$ (default `1.15`) and $S \ge 1$ and `verified_gate == True` transition to `"promoted"`.
- **Prune (Archive):** Genes with $\text{Fitness}(g) < \text{prune\_threshold}$ (default `0.35`) or $F > S + 2$ transition to `"archived"`.
- **Compile:** Top $K$ (`max_active_genes = 15`) promoted genes are injected between `<!-- EVLOP:START -->` and `<!-- EVLOP:END -->` markers in `AGENTS.md` / `CLAUDE.md`, and ultra-high-fitness genes ($S \ge 3$) can be exported as standalone skills under `skills/auto-<id>/SKILL.md`.

### 6.4 CLI Commands (`python -m evlop` / `evlop`)

1. `evlop init [--target-dir .]` — Creates `.evlop/` store and ensures `AGENTS.md` / `CLAUDE.md` have EVLOP evolution blocks.
2. `evlop recall "<query>" [--top 5]` — Searches active genes by keyword/tag + fitness rank so the agent can consult prior wisdom before acting (**Stage E**).
3. `evlop verify "<shell-command>"` — Executes a verification command, captures exit code & output, records `.evlop/last_verify.json` (**Stage V**).
4. `evlop log --task "..." --symptom "..." --root-cause "..." --fix "..." [--category ...] [--trigger ...] [--strategy ...] [--anti-pattern ...]` — Records an Episode and creates or reinforces a Gene, automatically checking `.evlop/last_verify.json` for verification proof (**Stage L**).
5. `evlop evolve [--target AGENTS.md,CLAUDE.md]` — Runs deduplication/merge, recalculates fitness scores, promotes/archives genes, and updates the `<!-- EVLOP:START -->...<!-- EVLOP:END -->` block in target markdown files (**Stages O & P**).
6. `evlop export-skill --gene-id <id> [--out-dir skills]` — Promotes a mature gene into a standard `SKILL.md` folder compatible with Claude Code and Antigravity (**Stage P**).
7. `evlop status [--json]` — Displays genome health, top genes, recent episodes, and evolution metrics.

### 6.5 Repository Directory Structure

```text
evlop/
├── README.md                          # Comprehensive Chinese documentation (Claude analysis + EVLOP + Papers + Quickstart)
├── README_EN.md                       # English documentation for international GitHub community
├── SKILL.md                           # Root Skill definition (drop-in for Antigravity / Claude Code)
├── AGENTS.md                          # Universal Agent instructions with live <!-- EVLOP:START --> block
├── CLAUDE.md                          # Claude Code specific configuration & EVLOP hook bindings
├── pyproject.toml                     # Standard Python packaging (zero external dependencies, console_scripts: evlop)
├── LICENSE                            # MIT License
├── docs/
│   ├── why-claude-is-strong.md        # Deep-dive analysis of Claude 5.2/5.5, Harness Co-design & Agentic RL
│   ├── evlop-methodology.md           # Full specification of the E-V-L-O-P 5-stage self-evolution loop
│   ├── papers-and-ecosystem.md        # Curated guide to 2023-2026 Self-Evolving Agent papers & GitHub repos
│   └── superpowers/
│       └── specs/
│           └── 2026-11-18-evlop-framework-design.md  # This design specification
├── templates/
│   ├── CLAUDE.template.md             # Ready-to-copy template for any repository
│   ├── AGENTS.template.md             # Ready-to-copy universal agent template
│   └── claude-settings-hooks.json     # Example Claude Code PostToolUse / Stop hooks for automatic EVLOP triggers
├── src/
│   └── evlop/
│       ├── __init__.py
│       ├── __main__.py                # Enables `python -m evlop`
│       ├── cli.py                     # CLI argument parser & command dispatcher
│       ├── models.py                  # Episode, Gene, VerifyResult, Config data structures
│       ├── fitness.py                 # Darwinian fitness scoring, similarity merge, promotion/pruning logic
│       ├── store.py                   # Atomic JSON/JSONL persistence & BM25/keyword recall search
│       ├── verifier.py                # Subprocess execution gate (`evlop verify`)
│       └── compiler.py                # Markdown marker injection (`AGENTS.md`/`CLAUDE.md`) & `SKILL.md` exporter
└── tests/
    └── test_evlop.py                  # Full unit & integration test suite verifying the entire E-V-L-O-P loop
```

---

## 7. What's Left to the Builder

- Exact formatting of CLI table output and Markdown section styling in compiled blocks.
- Pre-seeding an example `.evlop/` demonstration dataset or running a live end-to-end simulation during tests so users browsing the GitHub repo immediately see how promoted genes look inside `AGENTS.md` and `CLAUDE.md`.
- Git initialization (`git init`, commits on `main` branch) and providing a one-line `gh auth login && gh repo create` helper script if the local GitHub token requires interactive refresh.
