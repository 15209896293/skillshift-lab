# SkillShift 文档入口

## 当前产品主线

当前项目处于 SkillShift Studio R0 的规范收敛与 Foundation Spike 阶段。SkillShift 的主线是研究 Agent 对职业教育知识、能力、任务结构与人机协同的影响；Studio 是提供真实任务、受控 AI 协作、过程证据和教师干预入口的产品化研究基础设施。Python 是首条验证环境，不是整个项目的任务边界。当前仅有合成数据的本机基础验证；不进行部署、真实学生试用或研究系统实现。

产品定位已修订为“AI 协同作业过程治理”。先读下方产品决策记录；它在与较早的通用 Workspace 表述冲突时优先。

按顺序阅读：

1. `product/R0_PRODUCT_REPOSITIONING_DECISION.md`：当前产品定位、研究与 Studio 的层级关系、R0 闭环与不可宣称事项。
2. `product/TEACHER_ASSIGNMENT_REVIEW_REMIDIATION_WORKFLOW.md`：教师创建、复核、反馈和学生补正的通用 R0 工作流。
3. `product/R0_RESEARCH_TASK_EVIDENCE_CONTRACT.md`：R0 的 A+B 验证目标、任务责任、可观察事实和研究数据边界。
4. `product/REQUIREMENTS_SPEC.md`：当前 R0 需求基线；已统一教师 Web、学生 Node、提交包与复核闭环。
5. `architecture/TECHNICAL_SPEC.md`：当前技术 Draft；本机受限执行与数据边界须经 Spike 验证。
6. `quality/QUALITY_SPEC.md`：当前质量 Draft；约束 Node、数据、测试和安全边界。
7. `adr/ADR-001-hybrid-web-node-topology.md` 至 `ADR-003-submission-package-and-data-boundary.md`：形态决策及两项待验证边界。
8. `../specs/R0-FOUNDATION-SPIKE/README.md`：首个受限本机 Workspace Spike 的范围与验收。
9. `PROJECT_FILE_GOVERNANCE.md`：文件职责、状态、命名与新增文件放置规则。
10. `../SkillShift_Studio_软件工程总纲_V3.0.md`：产品方向、R0 边界和长期路线；待按决策记录完成一致性修订。

## 文档分层

| 路径 | 状态与用途 |
| --- | --- |
| `product/` | 当前 R0 产品需求规范。 |
| `architecture/TECHNICAL_SPEC.md` | 当前 R0 技术规范。 |
| `quality/` | 当前 R0 质量规范。 |
| `adr/` | 已确认或待确认的架构决策。 |
| `research/` | 保留的研究方法与证据资料；当前暂停扩展。 |
| `architecture/SYSTEM_ARCHITECTURE.md` 等 | 早期长期架构参考，不覆盖当前 R0 技术规范。 |
| `CURRENT_STATE.md` | 当前事实与下一步，不替代规范。 |
| `PROJECT_FILE_GOVERNANCE.md` | 文件层级、状态与生命周期规则；不替代产品或技术决策。 |

历史计划书位于 `../wenben/`，必须保留，不得覆盖或改写。
