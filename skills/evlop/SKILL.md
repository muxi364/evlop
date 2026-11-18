---
name: evlop
description: "Universal Self-Evolving Agent Framework & Darwinian Memory Engine distilled from Claude 5.2/5.5 and SOTA Self-Evolving Agent research. Use before, during, and after complex coding or debugging tasks to recall verified strategies, run deterministic verification gates, distill failure-to-fix trajectories into reusable genes, and auto-promote top rules into AGENTS.md, CLAUDE.md, and SKILL.md."
---

# EVLOP Self-Evolving Agent Skill

You have access to the **EVLOP** (`Execute & Explore -> Verify & Validate -> Learn & Log -> Orchestrate & Optimize -> Persist & Promote`) self-evolution framework. Use it to prevent repeating historical mistakes, eliminate hallucinated fixes, and continuously upgrade your own rules and skills across sessions.

---

## ⚡ Zero-Friction 2-Step Autopilot (Recommended for All Agents & Subagents)

Instead of running 6+ separate commands, any Agent can achieve world-class, Pareto-optimal results in **2 commands**:

1. **Step 1 — Before Coding (`preflight`):**
   Deconstructs the task into **Feynman First-Principles Invariants + Minimal Counter-Examples** AND recalls the top matching historical genes (`<50us` BM25 + CJK bigram index):
   ```bash
   python -m evlop preflight "<your task description>"
   # Or via MCP tool: evlop_preflight(task="<your task description>")
   # Or via Python SDK: engine.preflight("<your task description>")
   ```
2. **Step 2 — After Coding (`ship`):**
   Runs your test command + **100-Point AST Code Quality & $O(N^2)$ Complexity Gate**, and on pass **automatically distills, logs, governs, and promotes** the verified gene into `AGENTS.md` and `CLAUDE.md`:
   ```bash
   python -m evlop ship "<test command>" --code <path_to_file_or_dir>
   # Or via MCP tool: evlop_ship(command="<test command>", code="<path>")
   # Or via Python SDK: engine.ship("<test command>", code_path="<path>")
   ```

---

## The Granular 5-Stage EVLOP Protocol (Advanced Control)

### Stage 1: [E] Execute & Explore (Before Acting)

1. **Recall Prior Genes:** Before debugging an error or designing a non-trivial change, query your workspace genome:
   ```bash
   python -m evlop recall "<error keyword, module name, or symptom>"
   ```
2. **Isolate Exploration Context:** When exploring more than 5 unfamiliar files, delegate read-only reconnaissance to a subagent (`Explore` / `research`) so raw search noise does not pollute your main context window.

### Stage 2: [V] Verify & Validate (Mandatory Deterministic Gate)

Never claim a bug is fixed or a feature works based on reading your own diff. Run the deterministic verification gate:

```bash
python -m evlop verify "<test or build command, e.g. python -m unittest discover -s tests -v>"
```

- `evlop verify` captures the exact exit code, timestamp, and stdout/stderr digest into `.evlop/last_verify.json`.
- **Anti-Reward-Hacking Rule:** EVLOP refuses to promote any gene to permanent instructions unless `.evlop/last_verify.json` proves the verification command exited with code `0`.

### Stage 3: [L] Learn & Log (Distill Trajectory into an Episode & Gene)

Whenever you resolve a non-trivial bug, discover a repository convention, or recover from a failed attempt, log the `(Symptom -> Root Cause -> Fix)` trajectory immediately after `evlop verify` passes:

```bash
python -m evlop log \
  --title "<Short imperative rule title>" \
  --category "<debugging|architecture|testing|tooling|workflow>" \
  --task "<Brief task summary>" \
  --symptom "<Exact error message or failure symptom>" \
  --root-cause "<Why the failure happened>" \
  --fix "<What change solved it>" \
  --trigger "<When future agents should activate this gene>" \
  --strategy "<Concrete, repeatable instruction or command>" \
  --anti-pattern "<What failed or what to avoid>"
```

*(If a strategy you tried failed, pass `--failed` so its Darwinian fitness is penalized.)*

### Stage 4: [O] Orchestrate & Optimize (Darwinian Memory Governance)

Run the Darwinian governance engine to merge near-duplicate genes (Jaccard similarity $\ge 0.65$), recompute fitness scores with temporal decay, and prune stale rules:

```bash
python -m evlop status
```

### Stage 5: [P] Persist & Promote (Self-Upgrade Rules & Skills)

1. **Compile Top Promoted Genes into `AGENTS.md` and `CLAUDE.md`:**
   ```bash
   python -m evlop evolve --target AGENTS.md,CLAUDE.md
   ```
   This updates the bounded `<!-- EVLOP:START -->...<!-- EVLOP:END -->` block (capped at top 15 genes by fitness score).
2. **Incubate Mature Genes into Standalone Skills & Executable Tools (Voyager Mode):**
   When a gene reaches high empirical validation, export it as a standalone skill folder (pass `--synthesize-script` to also generate an executable `scripts/run_strategy.py` helper tool):
   ```bash
   python -m evlop export-skill --gene-id <gene-id> --out-dir skills --synthesize-script
   ```
3. **Evolve Child Gene Mutations & Inspect Phylogenetic Lineage (DGM Mode):**
   When refining an existing rule into a better Next-Gen strategy without destroying the ancestor in the archive:
   ```bash
   python -m evlop mutate --parent-id <parent-gene-id> --title "<New Gen Title>" --strategy "<Improved strategy>" --reason "<Why mutated>" --agent-id "<agent-name>"
   python -m evlop lineage --mermaid --out docs/LINEAGE.md
   ```
