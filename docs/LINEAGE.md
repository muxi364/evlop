# EVLOP Phylogenetic Lineage Tree (DGM Evolution Archive)

```mermaid
flowchart TD
    gene-bm25-corpus-idf-cjk-bigrams-3x-field-weigh["gene-bm25-corpus-idf-cjk-bigrams-3x-field-weigh<br/>Gen 1: BM25 Corpus IDF + CJK Bigrams + 3x Field Weighting for Recall<br/>Fitness: 1.35 (promoted)"]
    gene-self-healing-dag-node-retry-with-critical["gene-self-healing-dag-node-retry-with-critical<br/>Gen 3: Self-Healing DAG Node Retry with Critical Path Scorecard<br/>Fitness: 1.35 (promoted)"]
    gene-subagent-context-isolation-for-deep-explor["gene-subagent-context-isolation-for-deep-explor<br/>Gen 1: Subagent Context Isolation for Deep Exploration<br/>Fitness: 1.34 (promoted)"]
    gene-explicit-utf-8-encoding-on-cross-platform["gene-explicit-utf-8-encoding-on-cross-platform<br/>Gen 1: Explicit UTF-8 Encoding on Cross-Platform File I/O<br/>Fitness: 1.34 (promoted)"]
    gene-latency-profiled-execution-verification-ga["gene-latency-profiled-execution-verification-ga<br/>Gen 2: Latency-Profiled Execution Verification Gate<br/>Fitness: 1.35 (superseded)"]
    gene-execution-verified-patching-gate["gene-execution-verified-patching-gate<br/>Gen 1: Execution-Verified Patching Gate<br/>Fitness: 1.34 (superseded)"]
    gene-latency-profiled-execution-verification-ga -->|"Gen-3 HomeRail DAG resilience upgrad"| gene-self-healing-dag-node-retry-with-critical
    gene-execution-verified-patching-gate -->|"AlphaEvolve latency-aware verificati"| gene-latency-profiled-execution-verification-ga
```
