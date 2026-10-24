# SkillShift Lab

## 一句话说明

SkillShift Lab 是一个面向 Agent 时代的职业数字技能能力迁移项目；其当前产品入口是 SkillShift Studio。

它要解决的问题不是“让 AI 替代学生学习”，而是：当真实工作已经大量使用 Agent 时，学生如何把学校里学到的基础技能，迁移成能够与 Agent 协作完成复杂职业任务的能力。

首个试点方向是高职大数据技术。

## 这个项目现在处于什么阶段

当前阶段是：

**产品原型 R0 的规范与项目结构整理。**

R0 的目标不是建设完整教育平台、研究系统或与主流 Agent 竞争的通用开发平台。它先验证一个允许 AI 协同、但让作业过程可见、可复核、可干预的教学工作闭环：教师创建任务，学生在受控 Workspace 内完成 Python 练习，系统形成最小必要的过程证据，教师可要求解释或补正。Python 是首条验证环境，不是永久产品边界。

当前优先级：

1. 让 R0 的需求、技术和质量规范与已确认的产品重定位一致。
2. 以“教师 Web 端 + 学生桌面 Studio / Agent Node + 平台服务端”明确本机 Agent 与过程证据边界。
3. 用 Python 练习验证“创建—AI 协作—过程证据—教师复核—学生补正”的最小闭环。
4. 在独立同意、最小化与去标识化条件下，才讨论产品数据的研究使用。

## 项目核心思路

SkillShift 采用双轨任务结构。

| 轨道 | 目的 | 说明 |
| --- | --- | --- |
| Foundation Track | 确认学生已有基础能力 | 尽量限制 Agent，贴近课程、考试、考证和传统训练 |
| Agent Track | 训练人机协同职业能力 | 允许使用 Agent，但任务复杂度更高，重点观察委托、判断、验证、接管 |
| Transfer / Research | 研究能力迁移 | 比较基础能力、Agent 使用方式、验证行为和任务表现之间的关系 |

项目不默认进入正式课堂。第一阶段更适合第二课堂、课余实践、AI 兴趣小组、竞赛训练、专业拓展和就业技能训练。

## 目录说明

| 路径 | 用途 |
| --- | --- |
| `README.md` | 当前文件，整个项目的总入口 |
| `AGENTS.md` | 所有 Agent 必须遵守的规则 |
| `SkillShift_Studio_软件工程总纲_V3.0.md` | 当前产品方向总纲与 R0 边界 |
| `docs/README.md` | 当前文档入口与分层说明 |
| `docs/PROJECT_FILE_GOVERNANCE.md` | 文件职责、状态、命名与生命周期治理 |
| `docs/product/REQUIREMENTS_SPEC.md` | R0 用户背景、范围和验收标准 |
| `docs/architecture/TECHNICAL_SPEC.md` | R0 架构、技术选择、数据、API、目录规范 |
| `docs/quality/QUALITY_SPEC.md` | R0 代码、测试和安全规范 |
| `wenben/` | 原始项目计划书和历史文档，只保留，不随便改 |
| `docs/PROJECT_BRIEF.md` | 新 Agent 进入项目时优先阅读的稳定项目简报 |
| `docs/CURRENT_STATE.md` | 当前项目阶段、状态和下一步 |
| `docs/AGENT_DEVELOPMENT_FULL_CHAIN_AUDIT.md` | 面向项目负责人的 Agent 全链路开发审计 |
| `docs/PROJECT_STAGE_LONG_PLAN.md` | 项目阶段长计划和另一个 Agent 窗口的交接说明 |
| `docs/DEVELOPMENT_WORKFLOW.md` | Feature、Bug、Research、Refactor、Doc 的工作流程 |
| `docs/DEV_OS_AUDIT.md` | 当前 Dev OS 审计记录 |
| `docs/DEV_OS_IMPLEMENTATION_PLAN.md` | Dev OS 建设计划 |
| `docs/architecture/` | 当前有效或候选架构说明 |
| `docs/adr/` | 重要架构决策记录 |
| `docs/research/` | 研究流程、P0 协议、证据登记 |
| `docs/templates/` | 后续放任务、报告、评审等模板 |
| `specs/` | 每个 Feature、Research、Bug 或文档任务的规格 |
| `specs/P0-A/` | 第一个正式研究规格：传统实训任务 Agent 冲击审计 |
| `apps/` | 后续放前端、后端等应用代码 |
| `packages/` | 后续放共享库、类型、工具包 |
| `execution/` | 后续放 Sandbox、Verifier、Execution Adapter 相关实现 |
| `tests/` | 后续放测试、回归验证、端到端检查 |
| `artifacts/` | 后续放可复现的输出、审计结果、演示材料等非源代码产物 |
| `.github/` | GitHub Issue、PR、CI 模板 |

## 现有重要资产

`wenben/` 中的文件是项目战略和历史资产：

- `SkillShift_Lab_项目立项书暨研究开发文档_V2.2.docx`：前序研究主计划书，保留且不覆盖当前 R0 产品规范。
- `SkillShift_Lab_项目立项书暨研究开发文档_V2.0.docx`：历史版本。

这些文件不作为 Agent 每次开发都要全文读取的文件。日常开发优先读：

1. `README.md`
2. `AGENTS.md`
3. `docs/README.md`
4. `docs/product/R0_PRODUCT_REPOSITIONING_DECISION.md`
5. `docs/PROJECT_FILE_GOVERNANCE.md`
6. 当前任务对应的规范或 `specs/...`

## 如何使用 Agent 开发这个项目

最重要的规则：

**不要让 Agent “继续开发整个项目”。**

每次只给 Agent 一个边界清楚、可以验证的任务。

推荐提问格式：

```text
角色：
你现在担任 SkillShift 的 [角色]。

任务：
只做 [具体任务]。

上下文：
先读 docs/PROJECT_BRIEF.md、AGENTS.md 和 [指定 spec]。

允许范围：
[允许改哪些文件或目录]

禁止范围：
[明确禁止改哪些文件或方向]

验收标准：
[列出 PASS/FAIL 标准]

汇报：
必须说明文件变化、原因、测试命令、测试结果、已知限制、新风险、后续建议。
```

## Agent 完成任务时必须交付什么

Agent 不能只说“完成了”。

每次完成都必须交付：

- Task ID
- Files Changed
- Why
- Test Commands
- Test Results
- Acceptance Criteria PASS / FAIL
- Known Limitations
- New Risks
- Follow-up
- Git Diff Summary
- Commit，如果没有提交就写 `NONE`

## 研究材料状态

| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| P0-A 至 P0-E | 保留、暂停扩展 | 既有证据、任务和方法材料不删除，但不作为当前 R0 的实施前置门槛。 |

当前 R0 不输出“AI 替代率”、学生能力评分或研究结论；它只建立真实产品与最小必要的可追溯过程。

禁止输出“AI 替代率”。P0-A 的目标是理解任务变化、失败类型、人类介入点和可重构价值。

## Git 与 GitHub 状态

当前项目已经准备好进入 Git 管理。

注意：

- 不自动提交。
- 不自动推送。
- 不自动部署。
- 重大工作不要直接在 `main` 上开发。
- 后续并行 Agent 工作应使用“一 Issue = 一 Branch = 一 Worktree”。

## Spec Kit 使用原则

官方 GitHub Spec Kit 把三类工作作为独立入口：

- Spec-Driven Development：适合构建 Feature 或应用。
- Bug fixing：适合诊断和修复异常。
- Idea assessment：适合先判断一个想法是否值得投入。

SkillShift 不机械套完整流程。重大 Feature 走完整规格流程；小任务走轻量流程；研究任务走 Question -> Method -> Evidence -> Decision。

## Definition of Done

一个 Feature 只有同时满足以下条件，才能叫 Done：

- Spec requirement satisfied
- Acceptance Criteria passed
- Tests passed
- Lint / Typecheck / Build passed when available
- Converge passed
- No unresolved critical regression
- Required documentation updated
- Runtime or demo verification completed
- PR merged once GitHub workflow exists

在 GitHub PR 流程建立前，完成状态最多只能叫 `Verify`，不能叫正式 `Done`。

## 当前下一步

1. 审阅 `artifacts/R0-FOUNDATION-SPIKE/SPIKE_REPORT.md` 中的 PARTIAL 证据，特别是网络、进程树和符号链接限制。
2. 只在关闭 R0 Foundation Spike 的失败/部分通过项后，提出下一份“教师任务—学生协作—提交—复核—补正”的纵向闭环规格。
3. 不因已有参考 Node 而跳过受限执行验证、进入真实模型、真实学生数据或完整平台开发。

当前已完成 Git 初始化和 Dev OS 基线提交。R0 Foundation Spike 已开始并产生合成证据，但为 PARTIAL；本对话不开展真实学生试用、部署或研究执行。
