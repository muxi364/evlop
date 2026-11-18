# 自进化智能体（Self-Evolving Agents）顶会论文与开源生态全景索引（2023–2026）

本索引系统梳理了支撑 **EVLOP 框架** 的核心学术论文（arXiv / NeurIPS / ICLR / Nature / TMLR）以及 GitHub 上的顶级开源项目，按 EVLOP 五大阶段与演进维度分类。

---

## 一、 权威综述论文（Foundational Surveys, 2025–2026）

1. **A Survey of Self-Evolving Agents: What, When, How, and Where to Evolve on the Path to Artificial Super Intelligence**
   - **作者**：Huan-ang Gao et al. *(CMU, SJTU, Princeton, UIUC)*
   - **发表**：*Transactions on Machine Learning Research (TMLR)*, 2026 (`arXiv:2507.21046`)
   - **核心贡献**：提出了自进化智能体的四维分类学（*What to evolve*: 模型/记忆/工具/架构；*When to evolve*: 测试时内/测试时间；*How to evolve*: 文本反馈/标量奖励；*Where to deploy*），是 EVLOP 整体架构的理论母本。
   - **官方仓库**：[CharlesQ9/Self-Evolving-Agents](https://github.com/CharlesQ9/Self-Evolving-Agents)

2. **A Comprehensive Survey of Self-Evolving AI Agents: A New Paradigm Bridging Foundation Models and Lifelong Agentic Systems**
   - **作者**：Jinyuan Fang, Zaiqiao Meng et al.
   - **发表**：arXiv Preprint, 2025 (`arXiv:2508.07407`)
   - **核心贡献**：将静态基座模型与终身演进系统桥接为四个交互支柱（*System Inputs, Agent System, Environment, Optimizers*），直接启发了 EVLOP 的 `Verify -> Learn -> Optimize` 闭环。

3. **Self-Improvements in Modern Agentic Systems: A Survey**
   - **作者**：Zhe Ren et al.
   - **发表**：arXiv Preprint, 2026 (`arXiv:2607.13104`)
   - **核心贡献**：从系统工程视角剖析现代 Agent 如何通过自诱导更新算子（Self-induced Update Operators）将运行时轨迹转化为持久化的脚手架与参数增益。

---

## 二、 五大支柱里程碑论文（Milestone Papers Mapped to EVLOP）

| 论文简称 | 论文全称与出处 | 核心机制 | 在 EVLOP 中的工程映射 |
| :--- | :--- | :--- | :--- |
| **SWE-agent** | *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering* (Yang et al., NeurIPS 2024, `arXiv:2405.15793`) | 专为 Agent 设计的计算机交互接口（ACI）与真实沙盒测试反馈环 | **[E] & [V]**：`evlop verify` 确定性执行门禁与结构化报错截断 |
| **Reflexion** | *Reflexion: Language Agents with Verbal Reinforcement Learning* (Shinn et al., NeurIPS 2023, `arXiv:2303.11366`) | 语言强化学习（Verbal RL）：将失败轨迹转化为自然语言反思并存入情景记忆 | **[L] Learn & Log**：`evlop log` 的 `(Symptom -> Root Cause -> Fix -> Anti-Pattern)` 提取范式 |
| **TextGrad** | *TextGrad: Automatic "Differentiation" via Text* (Yuksekgonul et al., Nature 2025, `arXiv:2406.07496`) | 通过文本梯度（Textual Gradients）在复合 AI 系统中反向传播批评并更新提示词 | **[O] Optimize**：利用验证反馈更新基因的 `strategy` 与适应度权重 |
| **Voyager** | *Voyager: An Open-Ended Embodied Agent with Large Language Models* (Wang et al., 2023, `arXiv:2305.16291`) | 终身学习与可执行技能库（Skill Library）的持续积累与检索复用 | **[P] Promote**：`evlop export-skill` 将成熟基因固化为可复用的 `SKILL.md` 模块 |
| **ADAS** | *Automated Design of Agentic Systems* (Hu et al., ICLR 2025, `arXiv:2408.08435`) | 元智能体（Meta-Agent）在代码空间自动搜索、评估并演进新的 Agent 拓扑与规则 | **[P] Persist**：`evlop evolve` 自动重写宿主 Agent 的 `AGENTS.md` / `CLAUDE.md` 指令层 |
| **Darwin Gödel Machine (DGM)** | *Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents* (Sakana AI & Academic Collaborators, 2025–2026) | 冻结基座模型权重，用经验基准（SWE-bench）替代哥德尔形式化证明，递归重写 Agent 自身脚手架代码并维护谱系树，**将 SWE-bench 从 20.0% 自主演进至 50.0%** | **[V] + [O] + [P]**：经验适应度门禁 + 谱系归档（防局部最优陷阱） |
| **AlphaEvolve** | *AlphaEvolve: A Gemini-Powered Coding Agent for Designing Advanced Algorithms* (Google DeepMind, 2025–2026) | 结合进化搜索与确定性评估器（编译器/性能剖析器），自主发现打破 56 年 Strassen 记录的 $4 \times 4$ 复数矩阵乘法算法并优化数据中心调度 | **[V] Verify & [O] Optimize**：零容错确定性验证评估器驱动的代码与策略演化 |

---

## 三、 GitHub 顶级关联开源项目（Top Open-Source Repositories）

### 1. Claude Code 架构逆向与官方生态
- **[anthropics/claude-code](https://github.com/anthropics/claude-code)**：Anthropic 官方终端 Agent，展示了工业级 TAOR 循环与工具协同。
- **[VILA-Lab/Dive-into-Claude-Code](https://github.com/VILA-Lab/Dive-into-Claude-Code)**：深度拆解 Claude Code 内部设计模式、子智能体调度与上下文压缩机制。
- **[Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts)** & **[zep-us/claude-system-prompt](https://github.com/zep-us/claude-system-prompt)**：持续追踪 Claude 历代内置工具定义与 Subagent 系统提示词。

### 2. Agent 记忆演进与技能自进化先驱项目
- **[jack60810/claude-evolve](https://github.com/jack60810/claude-evolve)**：基于达尔文适应度评分（Darwinian Fitness Scoring）的 Claude Code 自进化系统，验证了高适应度规则自动晋升为 `.claude/skills/auto-*/`、低效规则自动衰减淘汰的工程可行性。
- **[EvoMap/evolver-claude-code-mods](https://github.com/EvoMap/evolver-claude-code-mods)**：提出基因组演进协议（Genome Evolution Protocol, GEP），为编码 Agent 提供跨会话的演化记忆。
- **[ethanbytes/Self-Evolving-Skill](https://github.com/ethanbytes/Self-Evolving-Skill)**：融合 MUSE 与 Mem0 分层记忆思想，通过 `add / merge / update / delete` 四类治理算子让 `SKILL.md` 在使用中动态进化。
- **[coleam00/claude-memory-compiler](https://github.com/coleam00/claude-memory-compiler)**：受 Andrej Karpathy 的 LLM Knowledge Base 启发，将会话日志自动编译为结构化知识库。
- **[mickeyyaya/evolve-loop](https://github.com/mickeyyaya/evolve-loop)** & **[evanklem/evanflow](https://github.com/evanklem/evanflow)**：引入确定性测试门禁与 TDD 迭代闭环，防止 AI 编写未经验证的代码。

### 3. 异构多智能体混合并发与 DAG 轨道编排（Heterogeneous Multi-Agent Concurrency & DAG Rails）
- **[xiaotianfotos/homerail](https://github.com/xiaotianfotos/homerail)**（**HomeRail**）：极具代表性的本地多智能体编排运行时。它摒弃了传统不可控的“多智能体聊天黑箱”，将多智能体协同转化为**显式有向无环图（DAG Rail）轨道**，通过拓扑波次并发调度异构智能体（如 Claude Code、Codex 等驱动 `hr dag`）、内置运行评估计分卡（`hr scorecard` / `hr eval-run`）与确定性回放（`hr replay`）。这一设计直接启发了 **EVLOP v3.0** 的 `evlop dag` / `evlop scorecard` / `evlop replay` 异构并发引擎。
- **[affaan-m/claude-swarm](https://github.com/affaan-m/claude-swarm)** & **[nwiizo/ccswarm](https://github.com/nwiizo/ccswarm)**：面向 Claude Code 与 Codex 混合集群的依赖图分解、Git Worktree 沙盒隔离与冲突检测框架。
- **[fcarucci/Swarm](https://github.com/fcarucci/Swarm)** & **[aumiqx/colony](https://github.com/aumiqx/colony)**：基于共享消息板（Message Board）与守护队列的多智能体异步协作与评审集群。

### 4. 自进化智能体论文合集仓库（Awesome Lists）
- **[CharlesQ9/Self-Evolving-Agents](https://github.com/CharlesQ9/Self-Evolving-Agents)**（TMLR 2026 综述官方仓库）
- **[XMUDeepLIT/Awesome-Self-Evolving-Agents](https://github.com/XMUDeepLIT/Awesome-Self-Evolving-Agents)**
- **[ANative-Lab/Awesome-Self-Evolving-Agents](https://github.com/ANative-Lab/Awesome-Self-Evolving-Agents)**
