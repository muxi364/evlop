# AGENTS.md — EVLOP Self-Evolving Agent Protocol

This project is equipped with the **EVLOP Self-Evolving Agent Engine** (`.evlop/evlop_runner.py`).
Follow the 5-stage loop on every coding or debugging task:

1. **[E] Explore & Recall:** Before acting or when hitting an error, run:
   `python .evlop/evlop_runner.py recall "<error or keyword>"`
2. **[V] Verify Deterministically:** Run your test/build command through the gate:
   `python .evlop/evlop_runner.py verify "<test-command>"`
   *(If verification fails, EVLOP automatically diagnoses the stack trace and recalls matching fixes!)*
3. **[L] Learn & Log:** After fixing a failure and passing `verify`, log the lesson automatically:
   `python .evlop/evlop_runner.py log --from-last-failure --title "<Rule Title>" --task "<Task>" --root-cause "<Why>" --fix "<How fixed>"`
4. **[O & P] Evolve & Promote:** Compile verified high-fitness genes into project instructions:
   `python .evlop/evlop_runner.py evolve --target AGENTS.md,CLAUDE.md,.cursorrules`

<!-- EVLOP:START -->
## EVLOP Evolved Genome (Auto-Compiled High-Fitness Rules)

> Managed automatically by `evlop evolve`. Only verified rules (`verified_gate=True`) with high Darwinian fitness are promoted here (capped at top 15 genes to prevent Context Rot).

### 1. [DEBUGGING] Use Decimal with ROUND_HALF_UP and 10,000 bps divisor for financial calculations (`gene-use-decimal-with-round-half-up-and-10-000` | Fitness: `1.74` | S/F: `2/0` | Gen `1`)
- **Trigger (When):** When encountering AssertionError in financial/billing tests or implementing monetary calculations involving Decimal, ROUND_HALF_UP, and basis points (bps)
- **Strategy (Do):** Always parse monetary inputs with decimal.Decimal, divide basis points (bps) by Decimal('10000') (10,000 bps == 100%), and quantize each intermediate calculation to Decimal('0.01') with rounding=ROUND_HALF_UP.
- **Anti-Pattern (Avoid):** Never use binary float, standard round() (which uses round-half-to-even), or divide basis points (bps) by 100 instead of 10,000.

<!-- EVLOP:END -->
