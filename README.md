# SkillShift Lab

> **2026-10-17 当前入口。** 本仓库已完成一次项目对齐：先读 [`docs/PROJECT_ALIGNMENT_2026-10-17.md`](docs/PROJECT_ALIGNMENT_2026-10-17.md)，再读 `AGENTS.md` 和对应的 Active R0 规范。下方保留了大量 2026-09-26 的历史回归摘要，**只能作为带日期的合成本机证据，不能作为当前源码、产品验收或研究结论的证明**。长期路线草案见 [`docs/PROJECT_ROADMAP_2026-10-17.md`](docs/PROJECT_ROADMAP_2026-10-17.md)。

## 一句话说明

SkillShift Lab 是一个面向 Agent 时代的职业数字技能能力迁移项目；其当前产品入口是 SkillShift Studio。

它要解决的问题不是“让 AI 替代学生学习”，而是：当真实工作已经大量使用 Agent 时，学生如何把学校里学到的基础技能，迁移成能够与 Agent 协作完成复杂职业任务的能力。

首个试点方向是高职大数据技术。

## 这个项目现在处于什么阶段

当前阶段是：

**截至 2026-10-09：R0 / R0.5 合成原型与证据边界整理。**现有控制面和 HTML 原型有截至 2026-09-26 的有限本机回归记录；另有一套 React + TypeScript + Vite 教师/学生 Web 工程，但 2026-10-09 交接只做了源码检查，未运行 build、lint、服务或完整浏览器流程。整体仍未验收，产品与代码执行边界见 [`docs/PROJECT_STATUS_2026-10-09.md`](docs/PROJECT_STATUS_2026-10-09.md)。

**最近记录的控制面验证（Tasks R0-P3-125–128，2026-09-26）：**Task125/126检查学生提交回执丢失后的刷新、显式选回任务、最近记录读取失败和局部重试；Task127检查教师发布回执丢失后的原请求重试与去重；Task128检查教师整页刷新后从仍运行的合成服务读回已发布任务，刷新没有再次发布。共37项浏览器断言通过，学生390px、教师1280px无横向溢出。全量回归 Python 213（212通过、1跳过）、Node 43/43；API 39/39、WSGI 11/11、前端静态48/48。均为本机合成内存与有限浏览器证据；Task128不验证服务重启恢复、真实网络或生产持久化，整体 R0 仍为 PARTIAL。完整报告与 Artifact 哈希见 `docs/CURRENT_STATE.md` 和 `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_P3_TASK_SWITCH_AND_REVIEW_ISOLATION_REPORT_2026-09-26.md`。

**历史快照（截至 Task066；旧记录，最新验证见下方）：R0 项目型教育 Agent 产品建设中。暂停回执未知时保留原 Workspace、修订号和幂等身份；教师多任务概览、任务级队列/补正/详情重试、未知总数提示和读取区域代次隔离已有代码与测试。Python 全量 204 项（203 PASS、1 SKIP），Node 客户端 41/41，Workspace API 35/35，WSGI 11/11，前端静态 43/43。此前 loopback 检查覆盖成功空目录、目录 503 后恢复为空、教师无复核队列、学生从 A 切换到 B 遇到 503 后保持 B 未知并重试恢复；A/B 草稿分别保留；另验证开始任务已在服务端生效但 503 回执丢失时，学生不能切走；重读明确确认 A 为 IN_PROGRESS 且不重复 start，暂停 A 后才可切到 B。教师多任务中的 A 补正读取 503 后，通过区域级单任务重试恢复；队列、历史和 C 补正记录保持不变。另验证 A 队列持续 503 时只重读 A，已选 B 详情、历史和补正区域保持不变。教师 Workspace 详情首读 503 后，重试只读取对应 Workspace，未重载队列、历史和补正。队列部分失败时导航计数显示未知符号，重试恢复后按已缓存各任务数量更新；详情渲染不再额外请求复核队列。另在教师重试 A 队列、补正和历史期间分别切换 B，三种延迟旧 A 失败回执均被丢弃，B 选择及其他成功任务结果保留。刷新后活动 A 不会被静默重选；明确重选恢复 IN_PROGRESS 且不重复 start，暂停后才可切到 B。教师任务中心、长标题/理由在 Chrome 132 的 360/390px 下无页面横向溢出，任务中心/复核页也在 759–761px、1079–1081px 边界及 1280px 检查；学生和教师主视图 1280px 无溢出。提交重试明确收到409时即使工作区读回待复核状态，仍显示冲突并释放错误重试锁；教师 A 事件重读延迟失败期间切换B后，迟到旧失败不覆盖B事件区。教师 A ACK 写入成功但503回执未知期间尝试切换B时仍绑定A；按原动作重试后才恢复B详情。学生接受建议回执未知时仅原 ACCEPT 可重试，拒绝/接管不可并发。 学生 A 最近提交和补正延迟重试失败期间切换 B，迟到错误均不会覆盖 B 的已确认状态。Task045 补正场景确认 B 为 IN_PROGRESS，且 B 的补正与最近提交均为空。Task048 另修复了学生任务加载器中不可达的活动任务切换防线，并由静态回归锁定检查顺序。Task052 验证教师 A 的延迟历史分页在切换 B、A 新首屏读取失败后返回，不会改写当前保留的50条历史；重试后仍可加载完整51条。UTF-8 超限标题/理由在提交前被阻止。证据见 `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_P3_TASK_SWITCH_AND_REVIEW_ISOLATION_REPORT_2026-09-26.md`。更多失败与重试组合仍待验证；320px 支持下限未定。整体 PARTIAL，仅本机合成、进程内存、非生产。**

Prior validation snapshot (Tasks `R0-P3-104` through `R0-P3-122`, 2026-09-26; superseded by Task125 above): Edge/Playwright Tasks117–119 verified isolated teacher event retry, browser-lost teacher feedback recovery, and overlapping history/remediation failures. Task121 exercised the current WSGI API through 22 actual loopback HTTP requests, including stale-publish rejection/no side effect and idempotent submission replay/no duplicate. Task122 completed teacher create/publish → explicit student select/start/submit → teacher request remediation → student response v2 → second remediation tied to v2 → student response v3 → teacher ACK → student closed-state readback in Microsoft Edge over the same `127.0.0.1` HTTP server; 23 assertions passed, 110 requests, widths 390/1280 without overflow. ACK closes the remediation linked to v3 and preserves the earlier RESPONDED remediation linked to v2; the run exposed and helped fix a state-transition gap. Current full regression after the fix: Python 213 tests (212 pass, 1 skip), Node 43/43, Workspace API 39/39, WSGI 11/11, frontend static 48/48; JS syntax, Python compileall, runner compiles, Schema JSON and `git diff --check` passed. The sole skip is Windows symlink-creation privilege and is not symlink-safety evidence. Artifact report SHA-256: `E8E07283E1C0F4A4B0A4C3EDF839BF41858A07DCD4593B6DAA94CCA9A6909AAC`. This is synthetic in-memory loopback HTTP/browser evidence, not production HTTP/authentication/persistence/security proof; demo routes are not authentication. No real identity/data/model/ECS/deployment or secure code execution. Overall PARTIAL. Owner decision remains needed before changing student-facing meanings for ENVIRONMENT_ISSUE, REQUEST_EXPLANATION or REQUEST_EVIDENCE. Commit: NONE.
此前现场回归（Tasks `R0-P3-A-STUDENT-WORKSPACE-STATE-LABELS-099` / `R0-P3-A-FAILED-START-NO-SIDE-EFFECT-100` / `R0-P3-C-STALE-TEACHER-EVENT-SUCCESS-101` / `R0-P3-A-STUDENT-STATE-LABEL-BROWSER-102` / `R0-P3-A-RESUBMITTED-CLOSED-UI-SYNC-103`，2026-09-26）：学生 Workspace 七种合法状态在显示层使用中文标签，状态机仍用原始 wire enum；提交处理同步更新任务卡和选择器状态。服务端双任务 API 回归证明 B 启动遭 409 时 A/B 状态、修订号、事件流不变；暂停 A 后以相同幂等键和 B 原修订号重试成功。Edge/Playwright 将实际 loopback A 事件非空 200 暂存，在明确切至 B 并读取 B 事件 200 后释放；B 选择、事件列表和状态不变。学生页浏览器检查了等待教师复核、等待补正、暂停、补交等待复核及本轮结束；完整合成补正→第2版提交→教师 ACK→学生刷新并明确重选，RESUBMITTED/CLOSED 均在两处状态区域可见。390px状态/闭环截图经视觉检查，视口无横向溢出。全量 Python 212 项（211通过、1跳过），Node 43/43、Workspace API 38/38、WSGI 11/11、前端静态 48/48；JS语法、Python编译、Harness py_compile、Schema JSON、git diff --check通过。唯一跳过是 Windows 无创建符号链接权限，不构成符号链接安全证据。Artifact SHA-256：`9C7D7BE766D6E8DA3284F78CE88DAFA125E512775C663BF25A8A9D54A7379634`。证据限本机合成内存、固定 demo 角色和有限浏览器视口，不代表持久化、生产集成或完整 P4；整体仍 PARTIAL；真实身份/数据/模型/ECS/部署/学生代码执行均未启用；无需负责人决定；Commit：NONE。

此前现场回归（Tasks `R0-P3-A-START-ASSIGNMENT-RECEIPT-BINDING-094` / `R0-P3-C-REVIEW-HISTORY-DIRECTORY-RETRY-BROWSER-095` / `R0-P3-C-STUDENT-SAME-WORKSPACE-STALE-REMEDIATION-096` / `R0-P3-C-STUDENT-SAME-WORKSPACE-STALE-LATEST-097`，2026-09-26）：开始回执绑定所选任务；教师历史目录 503 时保留已读历史并提供独立重试。学生 A→B（暂停 B）→A 后，同一 Workspace 的旧补正失败和旧最近提交失败均在新读取成功后才返回，均未覆盖 A 已确认状态；360×800 无横向溢出。Task097 将最近提交专用 Harness 延迟调至 15 秒以稳定竞态顺序，仅测试设施变化。完整回归 Python 210（209 通过、1 跳过）、Node 43/43、Workspace API 38/38、WSGI 11/11、前端静态 46/46；JS/Python 编译、Harness py_compile、Schema JSON、git diff --check 通过。唯一跳过为 Windows 无创建符号链接权限，不构成符号链接安全证据。历史 Artifact（Task096）：`853ABA26B54BC711BC1EA5CE7681415879E8AF38B44F48999D3F926AB46306FB`；上次 Task097 现场报告值：`8403B81CD8E99C0A4D2A76B37F4179E0929B1E3855B2480638D5F43F1AAB0E24`；本次固化原始 Harness 日志后的 Artifact SHA-256：`07E1E6C8B37DAB3A82E7AF13A1862DEE6EECDAB7A6BA703786773570267E2DB2`。原始 HTTP/stdout 日志及各自 SHA-256 已存入 Artifact 目录。有限本机合成浏览器证据不代表生产或完整 P4；整体仍 PARTIAL，无真实身份/数据/模型/ECS/部署或学生代码执行；Commit：NONE。

此前现场回归（Task `R0-P3-STALE-TEACHER-DETAIL-RETRY-072`，2026-09-26）：教师详情重试先刷新任务待复核队列，并核对同一提交 ID/版本/工作区仍处于待复核状态，再读取 Workspace 且仅在其为 REVIEW_REQUIRED/RESUBMITTED 时恢复操作。Edge 1280×900 loopback 合成验证中，首个详情 GET 延迟503后，另一合成教师 ACK 返回201；原教师重试后队列计数为0、详情隐藏、复核动作禁用，并明确提示该提交已不在待复核队列，没有发出过期复核写入。全量 Python209（208 PASS、1 SKIP），Node41/41、Workspace API38/38、WSGI11/11、前端静态45/45；三项 JS 检查、Python compileall、Schema JSON 与 git diff check 通过。唯一跳过是 Windows symlink 创建权限不足，不构成符号链接安全证据。Artifact SHA-256：`7067F9A614C922B2C47BC99F38DE158AF2B6CE50CE9B75B8547E2441C2912226`。教师事件时间线 A→B→A Edge 1280×900 合成验证亦通过：A 延迟旧重试503期间加载B，再返回A获得新200；旧503迟到后A仍选中、事件列表/成功状态不变。整体仍 PARTIAL；仅本机合成，不代表生产集成；Commit：NONE。

此前现场回归（Task `R0-P3-TEACHER-CATALOG-STALE-READ-069`，2026-09-26）：教师任务目录读取新增请求代次保护；迟到的旧成功/失败响应不再覆盖更新的任务卡片或状态，当前目录读取失败显示在任务列表专属状态区并提供独立重试，不覆盖其他教师区域状态。Edge loopback 合成验证：启动目录旧空响应延迟到任务创建/发布成功后返回，已发布卡片仍只显示一次且成功状态保留；再将迟到旧响应替换成503，成功卡片与状态仍不变；当前目录首读503则在任务列表专属区域显示未知，明确重试后以第二次GET恢复已发布的合成任务。Python 全量209（208 PASS、1 SKIP），Node41/41、Workspace API38/38、WSGI11/11、前端静态45/45；JS语法、Python compileall、Harness py_compile、Schema JSON与`git diff --check`通过。唯一SKIP为Windows无创建符号链接权限，不构成符号链接安全证据。Artifact SHA-256：`659C643F4B92868B4A5FD0072EE880622B91DDF9545159502EA2D5E16FD92C98`。整体仍PARTIAL；本机合成和进程内存范围，完整P4及生产集成未闭合；Commit：NONE。

此前现场回归（Task `R0-P3-ACTIVE-TASK-CONFLICT-AND-API-CONCURRENCY-066`，2026-09-26）：共享内存 WorkspaceApi 在同一进程实例内增加串行派发，三项并发回归验证活动任务互斥、相同幂等键只产生一次写入和重叠请求串行；学生页将明确的 `active_task_exists` 409 与读取未知分开显示，重新读取目录后保持未选择状态。Edge loopback 390px 动态验证 A 首次 start 回执503、重读恢复、暂停A、启动B、刷新后明确选择A返回409并显示可行动冲突；目录重读后无静默选择。现场回归 Python 208（207 PASS、1 SKIP）、Node 41/41、Workspace API 38/38、WSGI 11/11、前端静态 44/44；语法、compileall、Harness py_compile、Schema JSON 与 `git diff --check` 通过。唯一 SKIP 为 Windows 无创建符号链接权限，不构成符号链接安全证据。该锁仅覆盖同一进程的共享 API 实例，不证明多进程、持久化或生产并发。Artifact SHA-256：`90854323586C8CF9D4EB8978FC4E47C0BD0ACAA602695571B3D503D419EF18E4`。整体仍 PARTIAL；P4、320px 支持范围、生产集成和安全代码执行仍未闭合。Commit：NONE。

**此前已验证的 P4 视口快照（Tasks057/060）：**教师历史失败/重试页与学生空状态均在本机 Codex 浏览器 360px 复测时发现旧 `body min-width:360px` 与垂直滚动条组合造成 15px 横向溢出；已移除两页该约束。360px/390px 下教师页与学生空状态的根节点 scrollWidth 均等于 clientWidth；教师分页失败保留50条、局部重试和显式加载第51条也在两种窄视口验证。另在360px验证学生目录首读503显示未知/重试，重读后保持未选择任务。此为有限合成视觉证据，不代表完整 P4；320px 支持下限仍未决定。完整回归 Python 204（203 PASS、1 SKIP）、Node41、API35、WSGI11、前端静态43；Artifact Task057/060，SHA-256：`CFD202461B1CCAF7EF4A376EA2C2B6DF044451FE8322DE5592D30BA90ED45EE7`。

R0 不建设完整 LMS、研究数据平台，也不与主流 Agent 比通用能力。首个产品切片围绕职业项目：教师布置允许 AI 协作的任务，学生在独立项目工作空间中与 Agent 协作、检查和提交，教师依据任务相关证据复核并反馈。首个 Golden Path 暂用合成 Python + CSV 项目。代码编辑体验属于目标工作台；实际代码执行须通过独立安全 Gate，未验证前不运行学生项目。详细范围见 `docs/product/R0_PROJECT_AGENT_WORKSPACE_DECISION.md` 和 `specs/R0-PROJECT-AGENT-WORKSPACE/README.md`。

当前优先级：

1. 保持共享 API、Artifact 来源与完整性边界可复核；候选 fixture 尚未成为唯一权威来源。
2. 代码级 DTO 调用和 loopback WSGI 固定资源 allowlist 已接线；已有有限 HTTP/浏览器检查，但完整 P4 运行与视觉复核未通过或完成。
3. 继续逐区域审计 P3 剩余失败隔离和任务状态边界；本轮已覆盖教师详情与队列失败、A→B→A 迟到事件、队列跨任务 DTO、学生工作区错绑。完整 P4 窄屏/视觉矩阵仍待验证。教师/学生演示角色仍不是认证，API 仍为进程内存。
4. 真实模型、代码执行、真实用户、部署和研究数据分别受独立 Gate 管理。

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
| `SkillShift_Studio_软件工程总纲_V3.0.md` | Draft 总纲；与已确认 R0 决策冲突时以后者为准 |
| `SkillShift_项目总体规划与研究计划书_V1.0.md` | 项目规划参考稿；不覆盖 Active R0 决策 |
| `docs/README.md` | 当前文档入口与分层说明 |
| `docs/PROJECT_FILE_GOVERNANCE.md` | 文件职责、状态、命名与生命周期治理 |
| `docs/product/REQUIREMENTS_SPEC.md` | R0 用户背景、范围和验收标准 |
| `docs/product/R0_PROJECT_AGENT_WORKSPACE_DECISION.md` | 2026-09-25 确认的项目型 Agent 工作空间产品方向 |
| `docs/architecture/TECHNICAL_SPEC.md` | R0 架构、技术选择、数据、API、目录规范 |
| `docs/quality/QUALITY_SPEC.md` | R0 代码、测试和安全规范 |
| `wenben/` | 原始项目计划书和历史文档，只保留，不随便改 |
| `docs/PROJECT_BRIEF.md` | 新 Agent 进入项目时优先阅读的稳定项目简报 |
| `docs/CURRENT_STATE.md` | 当前项目阶段、状态和下一步 |
| `docs/PROJECT_STATUS_2026-10-09.md` | 有日期的分领域现状快照；测试数字注明证据日期 |
| `docs/AGENT_DEVELOPMENT_FULL_CHAIN_AUDIT.md` | 面向项目负责人的 Agent 全链路开发审计 |
| `docs/PROJECT_STAGE_LONG_PLAN.md` | 项目阶段长计划和另一个 Agent 窗口的交接说明 |
| `docs/DEVELOPMENT_WORKFLOW.md` | Feature、Bug、Research、Refactor、Doc 的工作流程 |
| `docs/DEV_OS_AUDIT.md` | 当前 Dev OS 审计记录 |
| `docs/DEV_OS_IMPLEMENTATION_PLAN.md` | Dev OS 建设计划 |
| `docs/architecture/` | 含 Active R0 技术规范及历史/候选架构参考；逐文件看状态 |
| `docs/adr/` | 重要架构决策记录 |
| `docs/research/` | 研究流程、P0 协议、证据登记 |
| `docs/templates/` | 后续放任务、报告、评审等模板 |
| `specs/` | 每个 Feature、Research、Bug 或文档任务的规格 |
| `specs/P0-A/` | 保留的研究规格；当前暂停扩展，不是 R0 实施前置 |
| `apps/agent-first/` | 确定性流程 Harness 与本机合成 Workspace API |
| `apps/teacher-web/`、`apps/student-web/` | 教师/学生静态合成原型 |
| `apps/studio-web/` | React + TypeScript + Vite Web 前端源码；尚无现场 build/完整浏览器验收证据 |
| `apps/student-studio/`、`execution/` | 独立 Foundation Spike 研究资产；不代表代码执行安全通过 |
| `skillshift-studio-ui/` | HTML UI 设计稿与视觉 token，不等于 React 页面验收 |
| `fixtures/` | 候选合成项目输入，不等于运行时唯一权威来源 |
| `packages/` | 预留共享库目录 |
| `tests/` | 现有自动化测试、回归检查和合成端到端证据 |
| `artifacts/` | 可复核的验证输出、审计记录与研究材料；按任务和证据日期查阅 |
| `.github/` | GitHub Issue、PR、CI 模板 |

## 现有重要资产

`wenben/` 中的文件是项目战略和历史资产：

- `wenben/项目计划书_源文件归档/SkillShift_Lab_项目立项书暨研究开发文档_V2.2.docx`：前序研究主计划书，保留且不覆盖当前 R0 产品规范。
- `wenben/项目计划书_源文件归档/SkillShift_Lab_项目立项书暨研究开发文档_V2.0.docx`：历史版本。

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

1. 教师、学生页面已有代码级 DTO 调用，直接 WSGI 测试和有限 loopback HTTP/浏览器检查覆盖合成发布、提交、教师复核、补正重提、任务切换、局部读取失败、暂停未知结果恢复和若干窄屏视图。教师同任务历史/事件旧请求隔离、教师 A 详情成功迟到不覆盖 B、学生 A/B 延迟提交与补正读回隔离，以及 Agent 回执待确认时阻止暂停/切换并将迟到成功回复留在 A，均有有限浏览器顺序证据；学生任务目录 503 未知/重试状态由 Task060 在 360px 实浏览器复核，重读后保留空选择，只有学生明确选择才显示对应工作区；补正 GET 503 与教师历史分页后续页 503 有既有 360/390px 实浏览器证据；Agent 请求待确认时的选择/暂停冲突提示、教师三任务概览与选中详情也已在 360/390px 全页截图检查。既有窄屏截图按视口宽度的历史几何记录不等于根节点 clientWidth 校验；Task057 移除了两页 body 360px 最小宽度；Task060 复核学生目录故障恢复。教师历史分页和学生目录未知/空状态在修复后通过 360px 根节点尺寸核对，其他状态尚未全部复测。其余空/长标题/断点视觉矩阵及同范围学生补正重读仍待验证。320px 修复后几何未知，产品支持边界未定义。候选 fixture 与页面副本尚未统一为唯一来源。
2. 保留并记录 Foundation Spike 的 PARTIAL 证据；只有未来引入本机代码执行时才继续关闭其安全项。
3. 不因首条闭环而跳过真实学生数据、部署或本机受限执行所需的独立决定与验证。

当前已完成 Git 初始化和 Dev OS 基线提交。Foundation Spike 仍为 PARTIAL；Agent-first 合成流程是测试 Harness，项目型教师/学生工作区原型也仅使用合成内容。本项目未开展真实学生试用、真实模型接入、部署或研究执行。
