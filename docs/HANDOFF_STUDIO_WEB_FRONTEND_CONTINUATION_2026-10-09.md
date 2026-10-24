# SkillShift Studio Web 前端续开发交接手册

## 0. 文档信息

- 日期：2026-10-09（Asia/Shanghai）
- Task ID：`HANDOFF-STUDIO-WEB-FRONTEND-CONTINUATION-2026-10-09`
- 用途：交接给新窗口，基于现有 UI/React 前端继续做有限范围开发、验证和演示准备。
- 当前评估方式：只读检查文件与契约；本次没有启动服务、构建、运行测试或做浏览器视觉验收。
- Commit：NONE

## 1. 先给下一窗口的结论

目前有两套前端资产：

1. `skillshift-studio-ui/`：四张独立 HTML 设计稿及视觉 token / 设计描述；
2. `apps/studio-web/`：React + TypeScript + Vite 的可运行 Web 前端工程，已接入本机合成 Workspace API 的调用代码。

所以当前状态不是“只有 UI 图”，也还不是“完整产品前端已验收”。较准确的表述是：**核心教师/学生页面和主要流程已有前端实现，接入的是本机合成 API；启动、构建、浏览器流程、视觉与响应式验收需要由续开发窗口现场完成。**

下一窗口应先以只读方式核对现状和启动条件，再选一个有明确验收条件的小范围前端任务。不要重做整个 UI，也不要把以下未实现能力补成模拟的“成功产品功能”。

## 2. 仓库现场快照

本次只读核对时：

- 分支：`codex/r0-teacher-task-authoring`
- HEAD：`c5d6081`
- `git status --porcelain`：11 条已跟踪状态项、117 条未跟踪路径项。
- 工作区有现存修改、未跟踪原型/证据/文档、历史 Word 删除状态。它们是用户资产；不得清理、重置、覆盖、批量移动、删除或自动提交。
- 多文件续开发按 `AGENTS.md` 优先考虑隔离 Worktree。新窗口启动时必须重新检查分支、状态和拟修改文件；本节数字只是 2026-10-09 的快照。

## 3. 当前前端资产地图

### 3.1 UI 设计稿

| 路径 | 内容 |
| --- | --- |
| `skillshift-studio-ui/pages/student-home.html` | 学生首页稿 |
| `skillshift-studio-ui/pages/student-workbench.html` | 学生工作台稿 |
| `skillshift-studio-ui/pages/teacher-designer.html` | 教师任务设计稿 |
| `skillshift-studio-ui/pages/teacher-review.html` | 教师复核稿 |
| `skillshift-studio-ui/colors_and_type.css` | 设计 token / 色彩与排版 |
| `skillshift-studio-ui/skillshift-studio-ui.design` | 设计源文件 |
| `skillshift-studio-ui/validation-report.json` | 设计资产的静态质量报告 |

该 JSON 报告显示无阻塞错误、10 条 soft warning，包括硬编码颜色和颜色 token 使用规则。它只说明该设计校验器对这些 HTML/CSS 文件的检查结果，不等于 React 实现的视觉验收、浏览器运行验收或用户验收。续开发者要先核实设计稿与 React 页面是否仍一致，不要把这份报告直接称为前端通过。

### 3.2 React Web 前端

路径：`apps/studio-web/`

- 技术：React 19、TypeScript、Vite、React Router、TanStack Query、Tailwind CSS 4、Radix UI。
- `src/main.tsx` 当前挂载 `RouterProvider` 与 Query Client；实际页面由 `src/router.tsx` 路由，不使用默认 Vite `App.tsx` 作为入口页面。
- Vite 开发端口：5173；`/api` 代理到 `http://127.0.0.1:8000`。
- `package.json` 提供 `dev`、`build`、`lint`、`preview` 脚本。
- 现有 `README.md` 仍是 Vite 模板说明，不是 SkillShift 启动手册。

页面路径：

| 角色 | 页面 | 路由 |
| --- | --- | --- |
| 学生 | 首页 | `/student` |
| 学生 | 项目工作台 | `/student/workbench` |
| 学生 | 提交记录 | `/student/submissions` |
| 学生 | 设置 | `/student/settings` |
| 教师 | 首页 | `/teacher` |
| 教师 | 任务设计器 | `/teacher/designer` |
| 教师 | 复核与反馈 | `/teacher/review` |
| 教师 | 设置 | `/teacher/settings` |

当前入口按 URL 直接进入学生或教师路由。代码中没有真实登录/身份认证证明，不应演示或描述成登录后按真实账号识别角色。

### 3.3 本机合成 API

| 路径 | 当前用途 |
| --- | --- |
| `apps/studio-web/src/api/` | 前端 API 客户端、DTO 类型、校验、映射和 React Query hooks |
| `apps/agent-first/agent_first/workspace_api.py` | 合成 Workspace API |
| `apps/agent-first/agent_first/workspace_wsgi.py` | WSGI Web 适配 |
| `apps/agent-first/run_workspace_api.py` | 本机演示服务启动脚本 |

前端 `API_ROOT` 是 `/api/v1/demo`，不是生产 API。服务脚本注明只绑定 `127.0.0.1`、数据存于进程内存、服务停止后数据清空。已有 API/WSGI/旧网页测试记录不能自动证明新 `apps/studio-web` 的构建或浏览器交互通过。

## 4. 已实现到什么程度

只基于源码静态检查，本次确认：

- 学生端包括任务首页、工作区、文件文本编辑、Agent 对话、建议接受/拒绝、提交、最近提交和补正信息等页面/组件。
- 教师端包括任务列表与创建/发布、复核队列、提交详情和教师反馈动作。
- API 类型检查把 artifact 限定为固定的合成文件；Workspace 与 Task DTO 要求 `execution_enabled === false`。
- 任务设计器当前只提供两种固定协作模式：问答、学生确认后采纳修改提议，并在页面注明当前是固定合成项目，用于 R0.5 演示。
- 前端错误状态代码区分服务不可用、冲突、拒绝和一般错误；React Query 的写操作不自动重试。
- 测试/验证脚本目录里的旧前端测试主要针对既有静态页面/共享客户端；本次没有发现专门覆盖 `apps/studio-web` 页面与完整浏览器路径的测试记录。

以上是代码结构和契约层的证据，不代表本机服务现在正在运行，也不代表这些交互已经由浏览器现场走通。

## 5. 明确未闭合的产品与前端边界

1. **真实代码执行未开放**：代码编辑器是文本编辑体验；当前 DTO 明确要求 `execution_enabled: false`。不要增加可用的真实运行按钮、伪造执行日志或把静态/模拟输出叫作真实验证结果。
2. **确定性任务验证器没有接入这套前端闭环**：当前代码检索未找到学生可触发的 verifier/run-verify API 流程。后续如实现，先确认其规格、输入输出契约、错误分类和安全边界。
3. **Transfer 迁移任务未形成前端闭环**：当前路由/前端源码未见迁移阶段页面或任务切换闭环。不要把它描述为已完成；如要纳入下一项开发，先检查对应产品决定和数据契约。
4. **真实 Agent 未接入**：现有后端包含确定性/合成引导路径；界面中的 Agent 对话不能称为真实模型能力。任何真实模型调用都要遵循 Gate B、密钥/数据/成本与授权边界。
5. **真实身份、生产持久化、真实学生数据、部署均未在本次前端检查中得到证明。**
6. **产品形态存在来源差异**：`docs/product/R0_PRODUCT_REPOSITIONING_DECISION.md` 描述学生桌面 Studio/Agent Node + 教师 Web；`docs/product/R0_PROJECT_AGENT_WORKSPACE_DECISION.md` 仍将桌面端/浏览器工作空间作为待评估形态；R0.5 handoff 推进教师/学生 Web 页面。本次 React 工程是 Web 前端这一事实明确，但它不自动决定长期产品形态。若续开发会影响技术路线，先报告冲突，不静默改成桌面应用或承诺纯 Web 为最终形态。
7. **任务级 Agent Policy 冲突仍在**：R0 Active 产品/教师流程要求教师选择固定协作模式；2026-10-06 handoff 建议白名单内逐任务配置。现有前端实现前者的两个固定模式。负责人未形成新决策前，不新增任意工具/能力权限配置。
8. **研究数据不等于运营日志**：Studio 里的事件/提交服务于产品运行，不自动成为 Lab 的研究数据。研究用途须经过独立授权、最小化、去标识化与版本治理。

## 6. 续开发前的建议顺序

### 第一步：现场确认，不先改代码

- 按项目要求重新读 `AGENTS.md`、README/文档治理、产品决策和当前状态；特别核对 `docs/HANDOFF_STUDIO_R0_5_GOLDEN_PATH_2026-10-06.md`、本文件和 `docs/HANDOFF_UI_FRONTEND_R0_5_2026-10-08.md`。
- 重新记录 `git status --short --branch`，明确本任务的目标文件与保护文件。
- 核对 `apps/studio-web` 启动方式、前后端代理、合成 fixture 与 `skillshift-studio-ui` 设计稿关系。
- 先列出当前能运行、静态实现、已测试、未验证和未实现项，不从代码外观推断完成度。

### 第二步：建立可重复的演示基线

- 从 `apps/studio-web/` 阅读 `package.json` 与实际入口；从 `apps/agent-first/` 阅读演示服务说明。
- 在隔离/本机演示条件下验证服务启动、前端 build/lint、本机教师创建发布→学生任务工作区→Agent 合成回复/学生确认→提交→教师复核/补正→学生回应的可用路径。
- 另外核验空列表、加载失败、提交冲突/不确定、补正、关闭等状态；优先记录截图/日志位置和有限视口尺寸。
- 明确哪些检查是静态、单元、集成、浏览器现场验证；不要把旧 `CURRENT_STATE.md` 数值当作本轮结果。
- 本交接只给出验证计划；这些检查本轮没有运行。

### 第三步：选择一个有规格的前端任务

优先处理**演示可用性和现有流程**中的一个具体缺口，例如启动/演示说明、错误状态可理解性、某个已有 API 动作的反馈状态或一项有规格支撑的响应式问题。不要同时启动全面视觉重做、后端重构、模型接入、Verifier/Transfer 新功能和桌面化。

若发现必须新增业务字段、Agent 权限、研究指标、验证 API 或迁移任务才能完成，应先写清决策依赖和最小方案，由负责人确定后再改。

## 7. 推荐验收口径

每个续开发任务应在开工前写具体验收。本次没有替后续任务宣称通过。最低建议包含：

- 本地可按说明启动；服务和演示数据来源清楚。
- 主流程每一步都由可见状态/回执确认，不靠成功 toast 掩盖未确认状态。
- 服务错误、版本冲突、验证失败、学生输入错误分别呈现，不混为同一种“任务失败”。
- 桌面与选定窄屏视口的关键控件可用，无横向溢出；记录确切尺寸和浏览器。
- 所有 Agent/数据/验证结果明确标注真实或合成；当前演示应标注合成。
- 没有真实代码执行、真实模型调用、真实身份/数据或部署范围的意外扩张。
- 修改文件只落在批准范围，最终审阅 diff；Commit 未授权时写 `NONE`。

## 8. 必读入口

1. `AGENTS.md`
2. `README.md`、`docs/README.md`、`docs/PROJECT_FILE_GOVERNANCE.md`
3. `docs/HANDOFF_STUDIO_R0_5_GOLDEN_PATH_2026-10-06.md`
4. `docs/HANDOFF_UI_FRONTEND_R0_5_2026-10-08.md`
5. `docs/product/R0_PRODUCT_REPOSITIONING_DECISION.md`
6. `docs/product/R0_PROJECT_AGENT_WORKSPACE_DECISION.md`
7. `docs/product/R0_AGENT_FIRST_DELIVERY_DECISION.md`
8. `docs/product/REQUIREMENTS_SPEC.md`
9. `docs/product/TEACHER_ASSIGNMENT_REVIEW_REMIDIATION_WORKFLOW.md`
10. `docs/product/R0_RESEARCH_TASK_EVIDENCE_CONTRACT.md`
11. `docs/architecture/TECHNICAL_SPEC.md`、`docs/quality/QUALITY_SPEC.md`
12. `apps/README.md`、`apps/studio-web/README.md`、`apps/studio-web/package.json`
13. `apps/studio-web/src/router.tsx`、`src/api/`、各页面组件、`apps/agent-first/run_workspace_api.py`

若 Active 文件互相冲突，按 `AGENTS.md` 来源优先级报告，不覆盖或静默选边。

## 9. 可交给新窗口的续开发提示词

```text
请接手 SkillShift Studio Web 前端续开发。先阅读 docs/HANDOFF_STUDIO_WEB_FRONTEND_CONTINUATION_2026-10-09.md 和其中的必读文档，再检查当前分支、Git 状态和 `apps/studio-web/` 的实际实现。

目标不是重做 UI，而是在保护现有资产的前提下，选定并完成一个有明确验收条件的前端续开发任务。开始编码前先报告：
1. 当前能运行/有源码/有测试/已浏览器验证/仍未验证的能力分别是什么；
2. 计划改动文件及保护文件；
3. 选定的一个具体任务、验收条件和验证方式；
4. 会影响实现的产品决策冲突。

已确认的实现事实：UI 稿位于 `skillshift-studio-ui/`；React 前端位于 `apps/studio-web/`；开发 API 代理至 loopback `127.0.0.1:8000`；前端 API 根路径是 `/api/v1/demo`；后端是内存合成服务。现有学生工作台、教师任务设计与复核有主要 API 接线代码，但本交接未运行 build、lint、服务或浏览器演示，因此不能称已现场验证。

边界：不把 Studio Web 说成已决定的最终桌面/Web 产品形态；不增加真实代码执行、模型调用、登录、真实学生数据、生产持久化或部署；不伪造 verifier 或 Transfer 能力；不将模拟结果说成真实证据。任务级 Agent 权限配置仍有 Active 文档冲突，负责人新决策前保留现有固定协作模式。运营事件不会自动进入 Lab 研究数据。

当前工作区有大量未提交资产，开始前重新检查 `git status --short --branch`。禁止 reset、clean、覆盖、批量移动、删除、自动提交或推送；多文件工作按项目规则优先隔离 Worktree。只处理选定任务范围，不顺带全面重构。

完成所选任务后，按 AGENTS.md 报告 Task ID、文件变化与原因、验证命令和真实结果、验收 PASS/FAIL、模拟/未接通边界、限制与风险、后续决策、diff 摘要、Commit（无则 NONE）。不要把静态检查或合成演示写成真实模型、生产安全、用户研究或 R0.5 Golden Path 通过。
```

## 10. 本交接的效力

本文件是基于 2026-10-09 只读源码检查的续开发入口，不是产品决策，不代表测试/浏览器验收已经通过，不授权真实模型、学生数据、代码执行、研究数据导出或部署。
