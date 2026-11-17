# EVLOP 自进化方法论完整规范（The EVLOP Methodology Specification）

**EVLOP** 是一套面向所有 AI 编程与任务智能体（Claude Code、Antigravity、Cursor、OpenHands、Codex 及自研 Agent）的**跨会话自进化（Self-Evolution）标准协议与确定性引擎**。

---

## 一、 什么是 EVLOP 五步自进化闭环？

```mermaid
flowchart LR
    E["[E] Execute & Explore<br>基因召回与子智能体隔离探索"] --> V["[V] Verify & Validate<br>确定性沙盒测试门禁"]
    V --> L["[L] Learn & Log<br>错题复盘与经验基因提取"]
    L --> O["[O] Orchestrate & Optimize<br>Jaccard去重与达尔文适应度计算"]
    O --> P["[P] Persist & Promote<br>晋升写入 AGENTS.md / 孵化 SKILL.md"]
    P -.->|"跨会话能力升级"| E
```

### 1. [E] Execute & Explore（沙盒探索与先验召回）
- **核心动作**：Agent 在动手修改代码或排查问题前，先执行 `evlop recall "<报错关键词或模块名>"`，从 `.evlop/genes.json` 中检索高适应度的历史经验基因。
- **上下文隔离原则**：当需要跨 5 个以上文件做广度搜索时，必须派生只读子 Agent 执行探索，仅将结论摘要带回主会话。

### 2. [V] Verify & Validate（确定性验证门禁）
- **核心动作**：严禁 Agent 仅凭肉眼阅读 Diff 就宣布修复成功。必须调用 `evlop verify "<测试或构建命令>"`。
- **防奖励黑客（Anti-Reward-Hacking）机制**：`evlop verify` 会将命令退出码（Exit Code）、时间戳与输出摘要写入 `.evlop/last_verify.json`。若最近一次验证未通过（`passed == False`），后续记录的任何经验基因的 `verified_gate` 均强制为 `False`，**永远无法晋升进入主提示词**。

### 3. [L] Learn & Log（轨迹复盘与基因提取）
- **核心动作**：受 **Reflexion**（语言强化学习）与 **TextGrad**（文本梯度反传）启发，当 Agent 经历了 `报错/受阻 -> 定位根因 -> 修复并通过验证` 后，立即调用 `evlop log` 将轨迹提炼为两个结构化实体：
  1. **Episode（事件轨迹）**：追加写入 `.evlop/episodes.jsonl`，保留完整的不可变审计日志。
  2. **Gene（经验基因）**：包含 `trigger`（触发条件）、`strategy`（标准动作）、`anti_pattern`（反模式禁忌）以及成功/失败计数。

### 4. [O] Orchestrate & Optimize（达尔文适应度治理与防腐烂）
为了彻底解决长程运行后规则文件无限膨胀（Context Rot），EVLOP 引入了形式化的**达尔文适应度函数（Darwinian Fitness Function）**：

$$\text{Fitness}(g) = \underbrace{\frac{S + 1}{S + F + 2}}_{\text{拉普拉斯平滑成功率}} \times \underbrace{\left(1 + 0.5 \cdot \ln(1 + S)\right)}_{\text{经验频次增益}} \times \underbrace{V_{\text{bonus}}}_{\text{确定性验证乘子}} \times \underbrace{2^{-\Delta t / H}}_{\text{时间半衰期衰减}}$$

- **参数定义**：
  - $S$：`success_count`（验证成功次数），$F$：`failure_count`（应用失败次数）
  - $V_{\text{bonus}}$：若通过 `evlop verify` 验证（`verified_gate == True`）则为 $1.5$，否则降权为 $0.8$
  - $\Delta t$：距离最近一次使用（`last_used_at`）的天数；$H$：半衰期天数（默认 $30$ 天）
- **自动去重合并（Jaccard Merge）**：当两条基因的 `title + trigger` 词元 Jaccard 相似度 $\ge 0.65$ 时，引擎自动合并两者，累加 $S$ 与 $F$ 并保留更详尽的策略描述。
- **生命周期流转**：
  - **Promoted（晋升）**：`verified_gate == True` 且 $S \ge 1$ 且 $\text{Fitness}(g) \ge 1.15$
  - **Archived（淘汰归档）**：$\text{Fitness}(g) < 0.35$ 或 $F > S + 2$
  - **Candidate（候选观察）**：其余处于观察期的基因

### 5. [P] Persist & Promote（规则持久化与技能孵化）
- **受控提示词编译（`evlop evolve`）**：将状态为 `promoted` 的基因按适应度降序排列，严格截取前 `max_active_genes`（默认 15 条），自动注入 `AGENTS.md` 与 `CLAUDE.md` 的 `<!-- EVLOP:START --> ... <!-- EVLOP:END -->` 标记块中。
- **独立技能孵化（`evlop export-skill`）**：受 **Voyager** 与 **ADAS** 启发，高适应度基因可通过 `evlop export-skill --gene-id <id>` 一键导出为标准的 `skills/auto-<id>/SKILL.md` 插件包，实现从“单条经验”到“模块化技能”的跃迁。
