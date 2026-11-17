# AGENTS.md — Project Agent Instructions (EVLOP Enabled)

## Self-Evolution Workflow (EVLOP)

1. **Before coding/debugging:** Run `python -m evlop recall "<query>"` or check the Evolved Genome block below.
2. **Before finishing:** Run `python -m evlop verify "<your test command>"` to record deterministic proof.
3. **When a bug or bottleneck is solved:** Run `python -m evlop log ...` followed by `python -m evlop evolve`.

<!-- EVLOP:START -->
## EVLOP Evolved Genome (Auto-Compiled High-Fitness Rules)

> Managed automatically by `evlop evolve`. Only verified rules (`verified_gate=True`) with high Darwinian fitness are promoted here (capped at top 15 genes to prevent Context Rot).

_No promoted genes yet. Run `evlop verify` -> `evlop log` -> `evlop evolve` to evolve rules._
<!-- EVLOP:END -->
