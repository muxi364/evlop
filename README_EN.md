# EVLOP: Universal Self-Evolving Agent Framework

<p align="center">
  <b>A Universal Self-Evolution Protocol & Darwinian Memory Engine for AI Agents</b><br>
  <i>Distilled from Claude 5.2 / 5.5 Harness Engineering & 2023–2026 Self-Evolving Agent Research</i>
</p>

<p align="center">
  <a href="./README.md">中文文档 (README.md)</a> ·
  <a href="./docs/why-claude-is-strong.md">Why Claude Is So Strong</a> ·
  <a href="./docs/evlop-methodology.md">EVLOP Specification</a> ·
  <a href="./docs/papers-and-ecosystem.md">Papers & Open-Source Ecosystem</a>
</p>

---

## 1. Overview

Why do Anthropic's frontier models (**Claude Fable 5.2 / Mythos 5.2** and **Claude Opus 5.5 / Sonnet 5.5**) combined with **Claude Code** dominate software engineering benchmarks like SWE-bench Verified (80%+ resolve rate)?

Because their intelligence is tightly coupled with **execution-guided verification loops**, **atomic tool harnesses**, and **strict context governance**. Yet most AI coding agents still suffer from **cross-session amnesia** (repeating yesterday's bugs) or **context rot** (append-only memory files that bloat prompts).

**EVLOP** solves both problems by providing a host-agnostic **Declarative Agent Protocol (`SKILL.md`, `AGENTS.md`, `CLAUDE.md`)** paired with a **Zero-Dependency Python Evolution Engine (`evlop`)** that any AI agent can invoke to continuously evolve its own rules and skills.

---

## 2. The 5-Stage EVLOP Loop

1. **[E] Execute & Explore:** Recall relevant high-fitness genes (`evlop recall`) before acting, and isolate broad file exploration inside read-only subagents.
2. **[V] Verify & Validate:** Run deterministic test/build gates (`evlop verify "<cmd>"`) that record cryptographic/exit-code proof into `.evlop/last_verify.json`. Unverified lessons can never be promoted.
3. **[L] Learn & Log:** Distill `(Symptom -> Root Cause -> Fix -> Anti-Pattern)` trajectories into `.evlop/episodes.jsonl` and `.evlop/genes.json` via `evlop log`.
4. **[O] Orchestrate & Optimize:** Automatically merge near-duplicate genes (Jaccard similarity $\ge 0.65$) and rank rules using the **Darwinian Fitness Formula**:
   $$\text{Fitness}(g) = \frac{S + 1}{S + F + 2} \times \left(1 + 0.5 \cdot \ln(1 + S)\right) \times V_{\text{bonus}} \times 2^{-\Delta t / H}$$
5. **[P] Persist & Promote:** Compile the top-$K$ (default 15) promoted genes directly into `AGENTS.md` and `CLAUDE.md` (`evlop evolve`) and incubate mature genes into standalone `SKILL.md` packages (`evlop export-skill`).

---

## 3. Quickstart

Requires **Python 3.10+** (standard library only, zero external `pip` dependencies):

```bash
# Initialize .evlop/ store in your workspace
PYTHONPATH=src python -m evlop init

# 1. [E] Recall prior genes
PYTHONPATH=src python -m evlop recall "UTF-8 encoding"

# 2. [V] Run deterministic verification gate
PYTHONPATH=src python -m evlop verify "python -m unittest discover -s tests -v"

# 3. [L] Log a verified lesson
PYTHONPATH=src python -m evlop log \
  --title "Explicit UTF-8 Encoding on Cross-Platform File I/O" \
  --category "debugging" \
  --task "Fix Windows locale encoding crashes" \
  --symptom "UnicodeDecodeError on Windows" \
  --root-cause "Default locale encoding in Path.read_text()" \
  --fix "Pass encoding='utf-8' explicitly"

# 4 & 5. [O & P] Govern genome and update AGENTS.md / CLAUDE.md
PYTHONPATH=src python -m evlop evolve --target AGENTS.md,CLAUDE.md

# Export a top gene into a standalone Skill
PYTHONPATH=src python -m evlop export-skill --gene-id gene-explicit-utf-8-encoding-on-cross-platform --out-dir skills
```

---

## 4. Academic & Open-Source Foundations

See [docs/papers-and-ecosystem.md](./docs/papers-and-ecosystem.md) for the complete literature review covering:
- **Surveys:** Gao et al. (*TMLR 2026*, `arXiv:2507.21046`), Fang et al. (`arXiv:2508.07407`), Ren et al. (`arXiv:2607.13104`)
- **Core Papers:** **SWE-agent** (*NeurIPS 2024*), **Reflexion** (*NeurIPS 2023*), **TextGrad** (*Nature 2025*), **Voyager** (*2023*), **ADAS** (*ICLR 2025*)
- **Open-Source Projects:** `anthropics/claude-code`, `VILA-Lab/Dive-into-Claude-Code`, `jack60810/claude-evolve`, `EvoMap/evolver-claude-code-mods`, `ethanbytes/Self-Evolving-Skill`, `coleam00/claude-memory-compiler`.

## License

[MIT](./LICENSE)
