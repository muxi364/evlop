# 跨 Agent 真实盲测与自进化实证报告（Cross-Agent Self-Evolution Empirical Verification Report）

为了验证 **“任何其他 AI Agent 在零外部依赖、零先验上下文的前提下，接入 EVLOP 后能否真正实现跨会话/跨智能体自进化”**，我们在独立的目标工程中执行了真实双智能体盲测实验（Two-Agent Blind Evolution Benchmark）。

---

## 一、 实验设计与工程环境

- **目标项目**：独立外部金融计费微服务仓库（包含未公开文档的领域潜规则：所有金额必须使用 `decimal.Decimal`、基点除数为 `10,000 bps = 100%`、且每个中间步骤必须按 `ROUND_HALF_UP` 量化到 `0.01`）。
- **接入方式**：仅执行一行命令完成跨项目零依赖注入：
  ```bash
  python -m evlop init --target-dir <target-project> --bootstrap --with-hooks
  ```
  自动在目标项目中生成：
  1. `.evlop/evlop_runner.py` 与 `.evlop/vendor/evlop/`（100% 零外部依赖独立运行器）
  2. `AGENTS.md`、`CLAUDE.md`、`.cursorrules`（含 EVLOP 5 阶段指令与受控基因块）
  3. `.claude/settings.json`（`SessionStart` 与 `Stop` 自动演化生命周期钩子）

---

## 二、 第一阶段盲测：`session-1-agent` 首次踩坑与基因沉淀

派发全新的独立子智能体 **`session-1-agent`** 进入工作区修复 `app/billing.py`：

1. **阶段 [E & V] 触发失败诊断**：
   `session-1-agent` 读取 `AGENTS.md` 后运行：
   ```bash
   python .evlop/evlop_runner.py verify "python -m unittest discover -s tests -v"
   ```
   引擎自动捕获 `AssertionError` 堆栈并写入 `.evlop/last_failure.json`（识别 `error_type = "AssertionError"`）。
2. **阶段 [V] 修复与确定性门禁通过**：
   `session-1-agent` 定位到二进制浮点数与基点除数问题，修复 `app/billing.py` 并重新运行 `verify`，获得退出码 `0` 与耗时证明。
3. **阶段 [L, O, P] 自动关联失败日志、晋升规则与合成技能脚本**：
   `session-1-agent` 执行 `log --from-last-failure --agent-id "session-1-agent"`、`evolve` 与 `export-skill --synthesize-script`：
   - **生成基因 ID**：`gene-use-decimal-with-round-half-up-and-10-000`
   - **初始达尔文适应度**：`1.3466`（`S=1, F=0, verified_gate=True, status="promoted"`）
   - **自动注入主文档**：成功写入 `AGENTS.md`、`CLAUDE.md` 与 `.cursorrules`
   - **自动合成 Voyager 可执行技能**：生成 `skills/auto-gene-use-decimal-with-round-half-up-and-10-000/SKILL.md` 及 `scripts/run_strategy.py`

---

## 三、 第二阶段盲测：`session-2-agent` 跨智能体零上下文继承与一击修复

销毁 `session-1-agent` 后，向项目中引入全新的退款模块 `app/refund.py`（包含同类领域缺陷），并启动**第二个完全独立的子智能体 `session-2-agent`（严禁其查看 `app/billing.py` 源码）**：

1. **验证失败瞬间触发 `[EVLOP Auto-Recall Hint]`**：
   当 `session-2-agent` 运行 `python .evlop/evlop_runner.py verify "python -m unittest discover -s tests -v"` 时，引擎在捕获 `tests/test_refund.py` 报错的同时，**毫秒级自动从基因库召回前序 Agent 留下的黄金基因并直接打印在终端**：
   ```text
   [EVLOP Auto-Recall Hint] Found 1 matching gene(s) for AssertionError:
     * Use Decimal with ROUND_HALF_UP and 10,000 bps divisor for financial calculations (gene-use-decimal-with-round-half-up-and-10-000): Always parse monetary inputs with decimal.Decimal, divide basis points (bps) by Decimal('10000') (10,000 bps == 100%), and quantize each intermediate calculation to Decimal('0.01') with rounding=ROUND_HALF_UP.
   ```
2. **一击修复（Zero-Shot Fix）与群体适应度跃升**：
   `session-2-agent` 无需翻阅其他代码或反复试错，直接应用召回的策略一次性修复 `app/refund.py` 并通过全部 3 项单元测试，随后执行 `log --from-last-failure --agent-id "session-2-agent"` 与 `evolve`：
   - **适应度跃升**：`1.3466` $\rightarrow$ **`1.7430`**（`S=2, F=0`）
   - **多智能体贡献溯源（`swarm_contributors`）**：`["session-1-agent", "session-2-agent"]`

---

## 四、 工程化保障矩阵汇总

| 工程能力维度 | 实现模块 | 解决的核心痛点 | 自动化测试覆盖 |
| :--- | :--- | :--- | :--- |
| **跨项目一键零依赖引导** | `src/evlop/bootstrap.py`<br>`evlop init --bootstrap --with-hooks` | 外部项目无需 `pip install` 或配环境变量，自带 `.evlop/evlop_runner.py` 独立运行 | `test_full_bootstrap_and_standalone_runner_in_external_project` |
| **报错栈自动解析与实时基因召回** | `src/evlop/verifier.py`<br>`extract_failure_diagnosis` | `evlop verify` 失败时自动提取异常类型并打印 `[EVLOP Auto-Recall Hint]` | `test_verify_failure_auto_diagnosis_auto_recall_and_from_last_failure_log` |
| **验证凭证 TTL 防伪锁** | `src/evlop/store.py`<br>`is_verify_fresh` | 超过 `verify_ttl_minutes`（默认 30 分钟）的陈旧验证凭证自动失效，杜绝跨会话伪造晋升 | `test_stale_verification_ttl_expiration_blocks_reward_hacking` |
| **跨进程/多线程并发排他锁** | `src/evlop/store.py`<br>`EvlopStore.lock()` | 结合线程 `RLock` 与 `.evlop/.lock` 原子文件锁，支持 6+ 子 Agent 并发写基因零丢失 | `test_concurrent_swarm_agent_logging_is_lock_safe` |
| **原生 MCP JSON-RPC 2.0 Server** | `src/evlop/mcp_server.py`<br>`python -m evlop mcp` | 为 Claude Desktop / Claude Code / Antigravity / Cursor 提供 5 个标准 MCP 工具调用接口 | `test_mcp_stdio_jsonrpc_server_tools` |
