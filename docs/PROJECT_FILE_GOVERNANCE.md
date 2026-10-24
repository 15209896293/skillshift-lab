# SkillShift 项目文件治理

## 状态与目的

- 状态：**Active**（2026-09-23）。
- 目的：为研究主线下的 Studio R0 建立单一、可追溯的文件入口和生命周期规则。
- 边界：本文件只治理文件职责与状态；不代表产品功能、技术选型或研究结论已经实现、验证或冻结。
- 本次治理不移动、不删除、不覆盖历史材料。目录迁移必须另行提出明确任务并做链接与引用检查。

## 先读什么

后续人员或 Agent 处理当前 R0 时，按下面顺序进入：

1. 根目录 `README.md`：项目目的、当前阶段与目录入口。
2. `docs/PROJECT_ALIGNMENT_2026-10-17.md`：当前项目主线、文件状态与工作顺序。
3. `AGENTS.md`：操作边界和证据要求。
4. `docs/README.md`：文档状态地图。
5. `docs/PROJECT_STATUS_2026-10-09.md`：带日期的现状快照；不能覆盖 Active 决策。
6. `docs/product/R0_PRODUCT_REPOSITIONING_DECISION.md`：当前已确认的产品方向。
7. `docs/product/R0_AGENT_FIRST_DELIVERY_DECISION.md` 与 `docs/product/R0_PROJECT_AGENT_WORKSPACE_DECISION.md`：首条闭环与项目型工作空间范围。
8. 本次任务直接相关的 Active 规范、ADR 或 `specs/` 文件。

如文件间存在冲突，不自行选择方便的一份；按 `AGENTS.md` 的来源优先级报告冲突。

## 目录地图

```text
SkillShift/
├─ README.md                         项目总入口（Active）
├─ AGENTS.md                         操作规则与来源优先级（Active）
├─ SkillShift_Studio_软件工程总纲_V3.0.md
│                                    产品总纲草案；已被重定位决策部分覆盖，待一致性修订（Draft）
├─ wenben/                           原始立项书、长期战略和历史版本（Historical / Preserve）
│  └─ 项目计划书_源文件归档/           V2.0/V2.2 历史 Word 源文件；保留原件
├─ docs/
│  ├─ README.md                      文档总入口与状态地图（Active）
│  ├─ PROJECT_FILE_GOVERNANCE.md     本文件（Active）
│  ├─ product/                       当前 R0 产品决策、工作流和需求规范
│  ├─ architecture/                  技术规范、架构边界和 ADR 的技术背景
│  ├─ quality/                       代码、测试、隐私与安全规范
│  ├─ adr/                           一项可追溯的决策及其理由；未经确认只能标 Proposed
│  ├─ research/                      研究协议、证据登记与方法材料（Preserve；当前暂停扩展）
│  ├─ templates/                     可复用模板，不承载实际任务事实
│  └─ CURRENT_STATE.md 等            状态、交接、审计和工作流程参考，不覆盖活跃规范
├─ specs/                            单一 Feature / Research / Bug / DOC 任务的可执行规格
├─ artifacts/                        可复现产物、审计记录、验证输出；不放源代码
├─ apps/                             现有合成流程、角色原型、React Web 与 Spike 资产（见下文）
├─ packages/                         未来共享类型、领域逻辑和工具包（Reserved）
├─ execution/                        本机受限进程安全 Spike；当前不授权运行学生项目
├─ tests/                            自动化测试、回归和端到端检查
└─ .github/                          Issue、PR、CI 配置（Reserved / GitHub 启用后使用）
```

现有 `apps/` 资产：`agent-first/` 是确定性流程 Harness 与本机合成 Workspace API；`teacher-web/`、`student-web/` 是静态角色原型；`studio-web/` 是 React + TypeScript + Vite 前端源码，尚无现场 build/完整浏览器验收；`student-studio/` 是独立 Foundation Spike 研究切片；`workspace-client.mjs` 是共享合成 API 客户端。`skillshift-studio-ui/` 保存独立 HTML 设计稿，`fixtures/` 保存候选合成项目输入。源码、设计稿、Harness 和 Fixture 是不同用途的资产，不应合并宣称为已验收产品。

仓库根目录另有 `tmp/` 和 Office 临时锁文件等现场资产；在确认内容、引用和所有者前保留原位，不纳入自动清理或目录迁移。

## 文档状态与单一事实来源

| 类别 | 当前文件 | 状态 | 使用规则 |
| --- | --- | --- | --- |
| R0 定位 | `docs/product/R0_PRODUCT_REPOSITIONING_DECISION.md` | Active | 与较早表述冲突时优先；只记录已确认决策。 |
| 当前项目对齐 | `docs/PROJECT_ALIGNMENT_2026-10-17.md` | Active | 当前阶段、文档导航、工作顺序与停止边界；不替代具体产品行为规范。 |
| 路线图 | `docs/PROJECT_ROADMAP_2026-10-17.md` | Proposed | 供负责人确认的长期推进顺序；不自动授权实施。 |
| 计划书版本索引 | `docs/PROJECT_PLAN_VERSION_INDEX_2026-10-17.md` | Active | 追溯 V1.0—V3.0 的位置和适用边界；不改写或替代历史计划书。 |
| R0 首条交付 | `docs/product/R0_AGENT_FIRST_DELIVERY_DECISION.md` | Active | 首条无本机自动执行的教学闭环边界；覆盖旧 Foundation 前置表述。 |
| R0 教师闭环 | `docs/product/TEACHER_ASSIGNMENT_REVIEW_REMIDIATION_WORKFLOW.md` | Active | 教师创建、复核、补正的行为基线。 |
| 研究—任务—证据契约 | `docs/product/R0_RESEARCH_TASK_EVIDENCE_CONTRACT.md` | Active | 连接 R0 A+B 验证、任务、人类责任、可观察事实与数据边界；不构成正式研究设计。 |
| 需求规范 | `docs/product/REQUIREMENTS_SPEC.md` | Active | 当前 R0 教学 Agent、最小提交包和复核闭环的产品基线。 |
| 项目状态快照 | `docs/PROJECT_STATUS_2026-10-09.md` | Snapshot | 汇总截至该日期的资产、证据日期、限制和 Git 快照；不替代 Active 规范，后续状态需新建或更新有日期的记录。 |
| 技术规范 | `docs/architecture/TECHNICAL_SPEC.md` | Active | Agent-first 合成闭环技术基线；本机执行另行验证。 |
| 质量规范 | `docs/quality/QUALITY_SPEC.md` | Active | Agent-first 闭环的测试、安全、隐私和证据基线。 |
| R0 ADR | `docs/adr/ADR-001-*` 至 `ADR-013-*` | Mixed | ADR-004 已确认首条交付边界；ADR-005 是已否决的 OpenAI 历史记录；ADR-006 至 ADR-010 分别记录模型、预算与 ECS 控制面边界；ADR-011/012 仅确认本机合成交互与持久化契约；ADR-013 已确认生产控制面部署门禁；其威胁模型仍为 Proposed；ADR-002/003 的受限执行和数据边界仍待验证。 |
| V3 产品总纲 | `SkillShift_Studio_软件工程总纲_V3.0.md` | Draft | 保留为总纲草案；不得覆盖重定位决策。 |
| 研究材料 | `docs/research/`、`specs/P0-A/`、`artifacts/P0-A/`、`wenben/` | Historical / Preserve | 保留证据链；当前不因 R0 而修改、迁移或宣称为已验证结论。 |
| 早期架构 | `docs/architecture/SYSTEM_ARCHITECTURE.md` 等 | Historical / Reference | 仅作背景；不覆盖当前 R0 技术规范。 |

没有明确标记为 Active 的文件，不得被默认当作当前实施要求。若一个事实需要同时出现在多处，应保留一份权威原文，其他位置只链接并说明适用状态。

## 新文件放置规则

| 要创建的内容 | 放置位置 | 命名与要求 |
| --- | --- | --- |
| 已确认的产品决策 | `docs/product/` 或 `docs/adr/` | 标注日期、状态、适用范围、冲突优先级。 |
| 未确认的技术方案 | `docs/architecture/` 或 `docs/adr/` | 必须标 `Proposed`，列出待决问题，不得伪装成已实现。 |
| 单次可实施事项 | `specs/<task-id>/` | 写清目标、范围、禁止项、验收与验证证据。 |
| 原始数据、运行日志、验证报告 | `artifacts/<task-id>/` | 与对应 spec / ADR 相互引用；不得把结论替代为原始证据。 |
| 运行时源代码 | `apps/`、`packages/`、`execution/` | 仅在独立实施规格获批后创建；不得用示例代码冒充产品实现。 |
| 测试代码 | `tests/` 或被测模块旁 | 与被测需求和验收项关联。 |

## 生命周期与禁止事项

1. 建立新方向时，先更新或新增一份权威决策，不能靠聊天记录、README 或代码注释承载决定。
2. 历史文档不“改写成当前版本”；需要新表述时新建活跃文档并明确旧文档状态。
3. 不把运行截图、日志或临时导出放进 `docs/`；它们属于 `artifacts/`。
4. 不在未获实施授权前向 `apps/`、`execution/`、`packages/` 写入产品代码。
5. 文件移动、删除、合并或大规模重命名属于独立变更：先盘点引用、保留回链、再执行验证。
6. 每次文档变更后，检查入口链接、状态描述和来源优先级是否仍一致。

## R0 开始工程前的文件门槛

在任何 R0 工程 Spike 前，至少应满足：

- 产品决策、教师工作流、需求/技术/质量三份规范彼此一致；
- R0 的执行位置（受管服务端执行、受限本机执行节点，或两者的边界）有一份明确的 Proposed/Accepted ADR；
- 有一个单一 Vertical Slice 的 `specs/` 任务，写明不处理的本机 IDE、虚拟机和外部 AI 边界；
- 对应的 `artifacts/` 验证位置与最小测试计划已指定。
