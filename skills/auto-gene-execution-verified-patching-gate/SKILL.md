---
name: auto-gene-execution-verified-patching-gate
description: "Auto-evolved EVLOP skill for [testing] Execution-Verified Patching Gate. Activate when encountering: Any code modification, bug fix, or refactoring task"
---

# Execution-Verified Patching Gate

> **EVLOP Auto-Evolved Skill** (`gene-execution-verified-patching-gate`)
> - **Category:** `testing`
> - **Darwinian Fitness:** `1.3466`
> - **Empirical Track Record:** `1` verified successes / `0` failures

## When to Trigger

Activate this skill whenever you encounter the following symptom, file pattern, or task context:

- Any code modification, bug fix, or refactoring task

## Verified Strategy (What to Do)

Run python -m evlop verify '<test-cmd>' and confirm exit_code == 0 before concluding

## Anti-Pattern (What to Avoid)

- Self-reporting success based solely on reading the code diff

## Evolution Lifecycle

If applying this skill resolves the task and passes `evlop verify`, reinforce it via:
```bash
python -m evlop log --title "Execution-Verified Patching Gate" --task "Applied auto-gene-execution-verified-patching-gate" --symptom "Any code modification, bug fix, or refactoring task" --root-cause "Known pattern" --fix "Run python -m evlop verify '<test-cmd>' and confirm exit_code == 0 before concluding"
```
