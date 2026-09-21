# SkillShift Lab

## 一句话说明

SkillShift Lab 是一个面向 Agent 时代的职业数字技能能力迁移项目。

它要解决的问题不是“让 AI 替代学生学习”，而是：当真实工作已经大量使用 Agent 时，学生如何把学校里学到的基础技能，迁移成能够与 Agent 协作完成复杂职业任务的能力。

首个试点方向是高职大数据技术。

## 这个项目现在处于什么阶段

当前阶段是：

**Dev OS 搭建 + P0 研究准备。**

也就是说，现在还不是正式开发完整平台的时候。当前最重要的是先把项目的开发方法、证据规则、Agent 协作方式和研究路线固定下来，避免后续多个 Agent 同时开发时互相污染文件、重复造真相，或者没有证据就声称完成。

当前优先级：

1. 建立最小可用的 Agent Native Development OS。
2. 准备 P0-A：高职大数据技术传统实训任务 Agent 冲击审计。
3. 用真实旧任务和证据判断 SkillShift 是否值得进入 MVP。
4. Gate 0 通过后，再开发第一个 SQL/MySQL 垂直切片。

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
| `wenben/` | 原始项目计划书和历史文档，只保留，不随便改 |
| `docs/PROJECT_BRIEF.md` | 新 Agent 进入项目时优先阅读的稳定项目简报 |
| `docs/CURRENT_STATE.md` | 当前项目阶段、状态和下一步 |
| `docs/AGENT_DEVELOPMENT_FULL_CHAIN_AUDIT.md` | 面向项目负责人的 Agent 全链路开发审计 |
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

- `SkillShift_Lab_项目立项书暨研究开发文档_V2.2.docx`：当前主计划书。
- `SkillShift_Lab_项目立项书暨研究开发文档_V2.0.docx`：历史版本。

这些文件不作为 Agent 每次开发都要全文读取的文件。日常开发优先读：

1. `docs/PROJECT_BRIEF.md`
2. `AGENTS.md`
3. `docs/CURRENT_STATE.md`
4. 当前任务对应的 `specs/...`

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

## 当前 P0 路线

| 阶段 | 目的 | 结果 |
| --- | --- | --- |
| P0-A | 收集 10 到 20 道真实传统实训任务，测试当前 Agent 会怎样影响它们 | Agent 冲击审计报告 |
| P0-B | 教师和学生需求验证 | 判断问题是否真实存在 |
| P0-C | 选择 3 道任务改造成双轨任务 | Foundation + Agent 任务规格 |
| P0-D | 做一个最小垂直切片 | Web + Sandbox + Agent + Verifier + Evidence |
| P0-E | 5 到 20 名学生课余 Pilot | 判断是否值得进入 MVP |

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

## 下一步建议

1. 初始化 Git，但不提交。
2. 检查当前文件结构。
3. 创建第一版提交前审计。
4. 开始 P0-A 任务清单模板。
5. 收集第一批真实传统实训任务。
