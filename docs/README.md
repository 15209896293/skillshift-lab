# SkillShift 文档入口

> **2026-10-17 当前文档入口。** 先读 [`PROJECT_ALIGNMENT_2026-10-17.md`](PROJECT_ALIGNMENT_2026-10-17.md)，它说明当前阶段、主线、证据边界与文件状态；计划书版本请查 [`PROJECT_PLAN_VERSION_INDEX_2026-10-17.md`](PROJECT_PLAN_VERSION_INDEX_2026-10-17.md)；再按其中的最小阅读顺序进入 Active R0 决策和任务规范。本文后续保留的 P3/Task 逐条记录均为历史证据索引，不是当前开发路线或当前验收状态。

项目根目录结构、常见目录用途和文件状态区分见 [`PROJECT_DIRECTORY_GUIDE_2026-10-24.md`](PROJECT_DIRECTORY_GUIDE_2026-10-24.md)。

## 当前产品主线

截至 2026-10-09 的分领域状态、证据日期和限制见 [`PROJECT_STATUS_2026-10-09.md`](PROJECT_STATUS_2026-10-09.md)。React Web 前端的最新只读源码交接见 [`HANDOFF_STUDIO_WEB_FRONTEND_CONTINUATION_2026-10-09.md`](HANDOFF_STUDIO_WEB_FRONTEND_CONTINUATION_2026-10-09.md)。

下文的 Tasks125–128 及测试计数均为 2026-09-26 的历史验证记录，不是 2026-10-09 重新运行结果。它们只覆盖特定本机合成内存/loopback 场景，R0/P3/P4 状态仍为 PARTIAL。

## 文件按什么用途查找

| 需要查找 | 位置 | 当前说明 |
| --- | --- | --- |
| 已确认产品方向与工作流 | `product/` | Active 决策和规格；冲突按 `AGENTS.md` 来源优先级处理。 |
| 状态、索引、交接 | `PROJECT_STATUS_2026-10-09.md`、`CURRENT_STATE.md`、`HANDOFF_*.md` | 状态快照与交接有日期；测试值须按证据日期理解。 |
| Web 设计与实现 | `../skillshift-studio-ui/`、`../apps/studio-web/` | 设计稿和 React 源码是不同资产；React 未经现场 build/浏览器验收。 |
| 合成流程原型 | `../apps/agent-first/`、`../apps/teacher-web/`、`../apps/student-web/` | 分开的 Harness/API/角色原型，不视为生产服务或认证。 |
| 研究、Spike、历史方案 | `research/`、`../specs/`、`../artifacts/`、`../wenben/` | 按各自状态保留；历史/Proposed 内容不自动成为当前实施要求。 |

最后记录的控制面现场回归见 [`CURRENT_STATE.md`](CURRENT_STATE.md) 与滚动证据报告。Tasks125/126 检查了学生提交回执丢失后的刷新、未到 API、最近记录读取失败和区域独立重试；Task127 检查教师发布回执丢失后的同请求重试；Task128 检查教师整页刷新后从仍运行的合成服务读回已发布任务且不重复发布。均为合成内存证据；Task128 不验证服务重启恢复或持久化。

Prior validation snapshot (Tasks `R0-P3-104` through `R0-P3-122`, 2026-09-26; superseded by Task125 above): Edge/Playwright Tasks117–119 verified isolated teacher event retry, browser-lost teacher feedback recovery, and overlapping history/remediation failures. Task121 exercised the current WSGI API through 22 actual loopback HTTP requests, including stale-publish rejection/no side effect and idempotent submission replay/no duplicate. Task122 completed teacher create/publish → explicit student select/start/submit → teacher request remediation → student response v2 → second remediation tied to v2 → student response v3 → teacher ACK → student closed-state readback in Microsoft Edge over the same `127.0.0.1` HTTP server; 23 assertions passed, 110 requests, widths 390/1280 without overflow. ACK closes the remediation linked to v3 and preserves the earlier RESPONDED remediation linked to v2; the run exposed and helped fix a state-transition gap. Current full regression after the fix: Python 213 tests (212 pass, 1 skip), Node 43/43, Workspace API 39/39, WSGI 11/11, frontend static 48/48; JS syntax, Python compileall, runner compiles, Schema JSON and `git diff --check` passed. The sole skip is Windows symlink-creation privilege and is not symlink-safety evidence. Artifact report SHA-256: `E8E07283E1C0F4A4B0A4C3EDF839BF41858A07DCD4593B6DAA94CCA9A6909AAC`. This is synthetic in-memory loopback HTTP/browser evidence, not production HTTP/authentication/persistence/security proof; demo routes are not authentication. No real identity/data/model/ECS/deployment or secure code execution. Overall PARTIAL. Owner decision remains needed before changing student-facing meanings for ENVIRONMENT_ISSUE, REQUEST_EXPLANATION or REQUEST_EVIDENCE. Commit: NONE.
此前现场回归（Tasks `R0-P3-A-STUDENT-WORKSPACE-STATE-LABELS-099` / `R0-P3-A-FAILED-START-NO-SIDE-EFFECT-100` / `R0-P3-C-STALE-TEACHER-EVENT-SUCCESS-101` / `R0-P3-A-STUDENT-STATE-LABEL-BROWSER-102` / `R0-P3-A-RESUBMITTED-CLOSED-UI-SYNC-103`，2026-09-26）：学生 Workspace 七种合法状态在显示层使用中文标签，状态机仍用原始 wire enum；提交处理同步更新任务卡和选择器状态。服务端双任务 API 回归证明 B 启动遭 409 时 A/B 状态、修订号、事件流不变；暂停 A 后以相同幂等键和 B 原修订号重试成功。Edge/Playwright 将实际 loopback A 事件非空 200 暂存，在明确切至 B 并读取 B 事件 200 后释放；B 选择、事件列表和状态不变。学生页浏览器检查了等待教师复核、等待补正、暂停、补交等待复核及本轮结束；完整合成补正→第2版提交→教师 ACK→学生刷新并明确重选，RESUBMITTED/CLOSED 均在两处状态区域可见。390px状态/闭环截图经视觉检查，视口无横向溢出。全量 Python 212 项（211通过、1跳过），Node 43/43、Workspace API 38/38、WSGI 11/11、前端静态 48/48；JS语法、Python编译、Harness py_compile、Schema JSON、git diff --check通过。唯一跳过是 Windows 无创建符号链接权限，不构成符号链接安全证据。Artifact SHA-256：`9C7D7BE766D6E8DA3284F78CE88DAFA125E512775C663BF25A8A9D54A7379634`。证据限本机合成内存、固定 demo 角色和有限浏览器视口，不代表持久化、生产集成或完整 P4；整体仍 PARTIAL；真实身份/数据/模型/ECS/部署/学生代码执行均未启用；无需负责人决定；Commit：NONE。

此前现场回归（Tasks `R0-P3-A-START-ASSIGNMENT-RECEIPT-BINDING-094` / `R0-P3-C-REVIEW-HISTORY-DIRECTORY-RETRY-BROWSER-095` / `R0-P3-C-STUDENT-SAME-WORKSPACE-STALE-REMEDIATION-096` / `R0-P3-C-STUDENT-SAME-WORKSPACE-STALE-LATEST-097`，2026-09-26）：开始回执绑定所选任务；教师历史目录 503 时保留已读历史并提供独立重试。学生 A→B（暂停 B）→A 后，同一 Workspace 的旧补正失败和旧最近提交失败均在新读取成功后才返回，均未覆盖 A 已确认状态；360×800 无横向溢出。Task097 将最近提交专用 Harness 延迟调至 15 秒以稳定竞态顺序，仅测试设施变化。完整回归 Python 210（209 通过、1 跳过）、Node 43/43、Workspace API 38/38、WSGI 11/11、前端静态 46/46；JS/Python 编译、Harness py_compile、Schema JSON、git diff --check 通过。唯一跳过为 Windows 无创建符号链接权限，不构成符号链接安全证据。历史 Artifact（Task096）：`853ABA26B54BC711BC1EA5CE7681415879E8AF38B44F48999D3F926AB46306FB`；上次 Task097 现场报告值：`8403B81CD8E99C0A4D2A76B37F4179E0929B1E3855B2480638D5F43F1AAB0E24`；本次固化原始 Harness 日志后的 Artifact SHA-256：`07E1E6C8B37DAB3A82E7AF13A1862DEE6EECDAB7A6BA703786773570267E2DB2`。原始 HTTP/stdout 日志及各自 SHA-256 已存入 Artifact 目录。有限本机合成浏览器证据不代表生产或完整 P4；整体仍 PARTIAL，无真实身份/数据/模型/ECS/部署或学生代码执行；Commit：NONE。

此前现场回归（Task `R0-P3-STALE-TEACHER-DETAIL-RETRY-072`，2026-09-26）：教师详情重试先刷新任务待复核队列，并核对同一提交 ID/版本/工作区仍处于待复核状态，再读取 Workspace 且仅在其为 REVIEW_REQUIRED/RESUBMITTED 时恢复操作。Edge 1280×900 loopback 合成验证中，首个详情 GET 延迟503后，另一合成教师 ACK 返回201；原教师重试后队列计数为0、详情隐藏、复核动作禁用，并明确提示该提交已不在待复核队列，没有发出过期复核写入。全量 Python209（208 PASS、1 SKIP），Node41/41、Workspace API38/38、WSGI11/11、前端静态45/45；三项 JS 检查、Python compileall、Schema JSON 与 git diff check 通过。唯一跳过是 Windows symlink 创建权限不足，不构成符号链接安全证据。Artifact SHA-256：`7067F9A614C922B2C47BC99F38DE158AF2B6CE50CE9B75B8547E2441C2912226`。教师事件时间线 A→B→A Edge 1280×900 合成验证亦通过：A 延迟旧重试503期间加载B，再返回A获得新200；旧503迟到后A仍选中、事件列表/成功状态不变。整体仍 PARTIAL；仅本机合成，不代表生产集成；Commit：NONE。

此前现场回归（Task `R0-P3-TEACHER-CATALOG-STALE-READ-069`，2026-09-26）：教师任务目录读取新增请求代次保护；迟到的旧成功/失败响应不再覆盖更新的任务卡片或状态，当前目录读取失败显示在任务列表专属状态区并提供独立重试，不覆盖其他教师区域状态。Edge loopback 合成验证：启动目录旧空响应延迟到任务创建/发布成功后返回，已发布卡片仍只显示一次且成功状态保留；再将迟到旧响应替换成503，成功卡片与状态仍不变；当前目录首读503则在任务列表专属区域显示未知，明确重试后以第二次GET恢复已发布的合成任务。Python 全量209（208 PASS、1 SKIP），Node41/41、Workspace API38/38、WSGI11/11、前端静态45/45；JS语法、Python compileall、Harness py_compile、Schema JSON与`git diff --check`通过。唯一SKIP为Windows无创建符号链接权限，不构成符号链接安全证据。Artifact SHA-256：`659C643F4B92868B4A5FD0072EE880622B91DDF9545159502EA2D5E16FD92C98`。整体仍PARTIAL；本机合成和进程内存范围，完整P4及生产集成未闭合；Commit：NONE。

此前现场回归（Task `R0-P3-ACTIVE-TASK-CONFLICT-AND-API-CONCURRENCY-066`，2026-09-26）：共享内存 WorkspaceApi 在同一进程实例内增加串行派发，三项并发回归验证活动任务互斥、相同幂等键只产生一次写入和重叠请求串行；学生页将明确的 `active_task_exists` 409 与读取未知分开显示，重新读取目录后保持未选择状态。Edge loopback 390px 动态验证 A 首次 start 回执503、重读恢复、暂停A、启动B、刷新后明确选择A返回409并显示可行动冲突；目录重读后无静默选择。现场回归 Python 208（207 PASS、1 SKIP）、Node 41/41、Workspace API 38/38、WSGI 11/11、前端静态 44/44；语法、compileall、Harness py_compile、Schema JSON 与 `git diff --check` 通过。唯一 SKIP 为 Windows 无创建符号链接权限，不构成符号链接安全证据。该锁仅覆盖同一进程的共享 API 实例，不证明多进程、持久化或生产并发。Artifact SHA-256：`90854323586C8CF9D4EB8978FC4E47C0BD0ACAA602695571B3D503D419EF18E4`。整体仍 PARTIAL；P4、320px 支持范围、生产集成和安全代码执行仍未闭合。Commit：NONE。

2026-09-26 P4 视口补充（Tasks057/060）：教师复核历史页与学生空/未知目录状态在360px本机浏览器检查发现，原 `body min-width:360px` 在垂直滚动条占宽时导致15px横向溢出；已移除两页该约束。360px/390px 下根节点 scrollWidth 与 clientWidth相等；教师历史分页失败保留50条、独立重试及显式加载第51条已验证。学生目录首读503后显示未知/重试，重读成功仍不自动选择任务。320px修复后几何未重测且支持范围未定义；P4整体仍 PARTIAL。完整证据与当前 SHA-256 见 Artifact 和 `CURRENT_STATE.md`。

此前阶段的已验证快照（Task057/060 前后）：Python 204 项（203 PASS、1 SKIP）、Node 客户端 41/41、Workspace API 35/35、WSGI 11/11、前端静态 43/43；当前现场值见上方 Task066。loopback 浏览器验证覆盖学生目录失败后成功空目录、教师无复核队列，以及学生暂停 A 后选 B 遇到 Workspace GET 503 时保留 B 选择、明确未知并重读恢复；A/B 编辑草稿隔离已在同一路径确认；Microsoft Edge 154 还验证开始任务已写入但 503 回执丢失后的未知态与重读恢复，未重复开始写入。教师 A 补正读取 503 后由单任务重试恢复，复核队列、历史和 C 补正结果保持原样；A 队列持续 503 时的单任务重试只访问 A 队列，已选 B 详情、历史和补正结果保持不变。活动 A 刷新后保持空选择，明确重选读取 IN_PROGRESS 且无重复 start；暂停 A 后才进入 B。Chrome 132 于 360/390px 检查相关失败/空状态无横向溢出；教师任务中心和复核页还抽查了 759/760/761、1079/1080/1081 与 1280px，学生/教师桌面主视图在 1280px 无溢出。教师表单按现有 Schema UTF-8 字节限额阻止超限标题/理由；任务中心和长文本状态也经窄屏验收。此前有限浏览器证据覆盖延迟 Agent 写入期间阻止切换、教师迟到详情不覆盖新选任务、分区读取失败/重试和多任务复核；详情及截图索引见 `../artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_P3_TASK_SWITCH_AND_REVIEW_ISOLATION_REPORT_2026-09-26.md`。更多失败重试组合仍待验证；320px 支持范围尚未定义，P4 未完成。仅本机合成、进程内存、固定 demo 角色非认证、非生产；共享 API 契约仍为 Proposed；代码执行仍须通过独立安全 Gate；真实模型、真实身份、真实数据与部署仍关闭。此前 Agent-first 合成闭环保留为流程 Harness，不代表生产工作台或真实 Agent 已实现。
此前已验证的 R0 阶段快照：Python 204 项（203 PASS、1 SKIP）、Node 客户端 41/41、Workspace API 35/35、WSGI 11/11、前端静态 43/43；当前现场计数见上方 Task066。暂停未知回执的状态读回及原修订号/幂等请求恢复已有有限 loopback 浏览器证据；另动态验证教师 Workspace 详情 503 可见失败及重试、同一任务较新的事件和历史读取成功不被延迟旧失败覆盖、同范围历史/事件失败重读保留上次成功结果，以及学生任务 A 的延迟提交和补正读回不覆盖任务 B。教师 A 详情成功迟到不覆盖 B 已有动态证据；学生 Agent 回执延迟期间切换/暂停已被阻止，成功回复只出现在 A，暂停后切到 B 未泄漏 A 对话。教师三任务概览与选中 B 详情、快照和事件已在 360/390px 全页浏览器检查。P4 未完成。历史 Chrome 132 几何检查曾记录 320px 页面溢出 40px；Task057 已移除学生和教师页 360px body 最小宽度，但本次未复测 320px，因此该修复后的几何状态未知，320px 产品支持范围仍未定义。教师三任务队列/补正隔离、51 条历史分页后续页 503 后保留首屏并重试恢复、学生任务目录/补正读取 503 后的未知状态与重试、提交后最近记录读回失败保留已在合成浏览器验证；任务目录重试后不会隐式选择任务，必须由学生明确选择。既有目录、补正失败、历史分页失败及学生 Agent 待确认冲突截图按当时视口宽度记录；Task057/060 后用 root clientWidth/scrollWidth 确认教师历史分页和学生目录未知/空状态在360px无横向溢出，其他状态尚未全量复测。补正成功后的同任务刷新暂没有界面入口。其余长标题、空/冲突等响应式视觉矩阵仍缺。详情和截图索引见 `../artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_P3_TASK_SWITCH_AND_REVIEW_ISOLATION_REPORT_2026-09-26.md`。本机合成、进程内存、固定 demo 角色非认证、非生产；共享 API 契约仍为 Proposed；代码执行仍须通过独立安全 Gate；真实模型、真实身份、真实数据与部署仍关闭。此前 Agent-first 合成闭环保留为流程 Harness，不代表生产工作台或真实 Agent 已实现。

P3 历史阶段证据（2026-09-26；最新计数与并发/冲突状态见上方 Task066）：Artifact `../artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_P3_TASK_SWITCH_AND_REVIEW_ISOLATION_REPORT_2026-09-26.md` 记录任务暂停/切换、学生开始和提交未知回执、教师多任务局部读取/重试以及延迟旧请求隔离；本次现场回归为 Python 204（203 PASS、1 SKIP）、Node 41/41、Workspace API 35/35、WSGI 11/11、前端静态 43/43。提交明确 4xx 被拒绝时，即使读回任务处于待复核态，也保留拒绝/冲突提示并释放错误重试锁。 教师事件区域延迟旧失败在切换任务后返回也已动态验证，不覆盖新任务成功事件。 教师复核写入成功但首回执丢失期间切换，也继续绑定原任务与动作；原幂等重试后才释放。学生提案接受仍未确认时拒绝/接管按钮保持锁定。 学生 A 最近提交及补正区域延迟旧失败在切换到 B 后返回，均不覆盖 B 的已确认状态；Task045确认 B 为 IN_PROGRESS，补正及最近提交为空。Task048将活动任务切换防线移至学生工作区加载入口的状态清理之前，并增加静态回归。Task052验证教师历史分页延迟成功与新一代首屏503交错后，旧分页不改写当前50条保留结果，重试后仍可加载第51条。整体 R0 P3/P4 仍 PARTIAL，本机合成，不代表生产或安全代码执行。

交接给新的主控 Agent 时，先使用 `HANDOFF_R0_AGENT_FIRST_CONTROL_PLANE_2026-09-24.md`；它补充较早的 Foundation 交接记录，并列出当前网页、控制面契约和可复跑证据。

产品定位已修订为“AI 协同作业过程治理”。先读下方产品决策记录；它在与较早的通用 Workspace 表述冲突时优先。

按顺序阅读：

1. `product/R0_PROJECT_AGENT_WORKSPACE_DECISION.md`：当前项目型 Agent 首个产品切片决策。
2. `../specs/R0-PROJECT-AGENT-WORKSPACE/README.md`：教师、学生、控制面和执行安全分层的产品规格。
3. `../specs/R0-TEACHER-WORKSPACE/README.md`：首个教师端前端任务与验收。
4. `../specs/R0-STUDENT-WORKSPACE/README.md`：学生代码编辑、Agent 建议、提交与执行关闭边界。
5. `../specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`：共享 API/领域对象草案与合成控制面接口边界（Proposed）；`workspace-api-v1.schema.json` 是本机合成 wire DTO 的严格 JSON Schema。
6. `product/R0_PRODUCT_REPOSITIONING_DECISION.md`：研究与 Studio 的层级关系及禁止推断边界。
7. `product/R0_AGENT_FIRST_DELIVERY_DECISION.md`：原确定性合成流程 Harness 的边界与历史 Gate；代码编辑范围由 2026-09-25 新决策扩展，执行仍未开放。
8. `product/TEACHER_ASSIGNMENT_REVIEW_REMIDIATION_WORKFLOW.md`：教师创建、复核、反馈和学生补正的通用工作流。
9. `product/R0_RESEARCH_TASK_EVIDENCE_CONTRACT.md`：任务责任、可观察事实和研究数据边界。
10. `product/REQUIREMENTS_SPEC.md`、`architecture/TECHNICAL_SPEC.md`、`quality/QUALITY_SPEC.md`：R0 需求、技术与质量基线及本轮范围修订。
11. `adr/ADR-006-domestic-multi-model-gateway-and-credential-boundary.md`：Gate B 已确认的国产多模型网关、学校统一 Key、教师可选 BYOK、学生无 Key 与基础降级边界；`adr/ADR-007-deepseek-first-synthetic-provider-contract.md`：首个 DeepSeek 合成探针的固定请求边界；`adr/ADR-008-deepseek-hosted-synthetic-runtime-authorization.md`：学校统一付费的托管合成运行时默认拒绝边界；`adr/ADR-009-school-synthetic-probe-budget-permit.md`：100 元月度硬上限的本地预算许可契约；`adr/ADR-010-ecs-control-plane-and-managed-secret-boundary.md`：ECS 控制面、托管密钥与非执行器边界；`adr/ADR-011-local-synthetic-web-prototype-boundary.md`：本机教师/学生网页与 API 原型的无部署边界；`adr/ADR-012-synthetic-control-plane-persistence-contract.md`：合成持久任务与预算预留的无部署契约；`adr/ADR-013-production-control-plane-readiness-gate.md`：已确认的生产控制面部署门禁；`architecture/PRODUCTION_CONTROL_PLANE_THREAT_MODEL.md`：仍待验证的 Proposed 威胁模型；`product/DOMESTIC_EDUCATION_AGENT_MODEL_ROUTE_RESEARCH.md` 保留其公开研究证据。ADR-005 是已否决的 OpenAI 历史记录。
12. `../specs/R0-AGENT-FIRST-VERTICAL-SLICE/README.md`：首条合成闭环的实施与验收规格；`../specs/R0-LOCAL-WEB-PROTOTYPE/README.md`：该闭环的本机教师/学生网页交互规格与验证范围；`../specs/R0-TEACHER-TASK-AUTHORING/README.md`：教师在合成模板上配置有限任务文字的 Gate A 扩展；`../specs/R0-SYNTHETIC-CONTROL-PLANE-PERSISTENCE/README.md`：持久化与预算预留的合成契约；`../specs/R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT/README.md`：敏感内容、日志与审计的本机安全契约；`../specs/R0-SYNTHETIC-BUDGET-LIFECYCLE/README.md`：预算预留、释放、待对账和结算的本机合成状态机契约；`../specs/R0-DEEPSEEK-USAGE-BOUNDARY/README.md`：请求上限、usage 解析和本地成本估算边界；`../specs/R0-PRODUCTION-CONTROL-PLANE-READINESS/README.md`：部署前置清单规格；`../artifacts/R0-ECS-OPERATIONS-READINESS-PLAN/OPERATIONS_READINESS_PLAN_2026-09-24.md`：ECS 服务加固、部署回滚与监控的 Proposed 运维计划；`../specs/R0-DEEPSEEK-BUDGET-RECONCILIATION-RESEARCH/README.md`：供应商费用对账和动态价格的 Proposed 研究。
13. `../specs/R0-FOUNDATION-SPIKE/README.md`：后续本机 Code Workspace 的安全 Spike 范围与证据。
14. `PROJECT_FILE_GOVERNANCE.md`：文件职责、状态、命名与新增文件放置规则。
15. `../SkillShift_Studio_软件工程总纲_V3.0.md`：产品方向、R0 边界和长期路线；待按决策记录完成一致性修订。

## 文档分层

| 路径 | 状态与用途 |
| --- | --- |
| `product/` | 当前 R0 产品需求规范。 |
| `product/R0_PROJECT_AGENT_WORKSPACE_DECISION.md` | Accepted：项目型 Agent 工作空间切片；代码执行另过安全 Gate。 |
| `../specs/R0-PROJECT-AGENT-WORKSPACE/README.md` | Active：教师、学生和后台协作的产品范围。 |
| `../specs/R0-TEACHER-WORKSPACE/README.md` | Active：首个教师前端合成原型规格。 |
| `../specs/R0-STUDENT-WORKSPACE/README.md` | Active：学生项目工作区合成原型规格；代码执行关闭。 |
| `../specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | Proposed：共享 API/领域对象草案；两端代码级 DTO 调用已有测试，WSGI 直接调用不代表已启动 HTTP 服务、浏览器通过、真实身份或生产设计。 |
| `../specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json` | Strict local wire DTO schema; test-only validator dependency is listed in `../requirements-test.txt` and is not an application runtime dependency. |
| `../fixtures/orders-audit-v1/` | Candidate synthetic project source with SHA-256 manifest; not yet consumed by API or teacher UI and not an accepted canonical source. |
| `architecture/TECHNICAL_SPEC.md` | 当前 R0 技术规范。 |
| `quality/` | 当前 R0 质量规范。 |
| `adr/` | 已确认或待确认的架构决策。 |
| `research/` | 保留的研究方法与证据资料；当前暂停扩展。 |
| `architecture/SYSTEM_ARCHITECTURE.md` 等 | 早期长期架构参考，不覆盖当前 R0 技术规范。 |
| `CURRENT_STATE.md` | 当前事实与下一步，不替代规范。 |
| `PROJECT_FILE_GOVERNANCE.md` | 文件层级、状态与生命周期规则；不替代产品或技术决策。 |

历史计划书位于 `../wenben/`，必须保留，不得覆盖或改写。
