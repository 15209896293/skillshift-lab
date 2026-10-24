# SkillShift 项目现状（2026-10-09）

## 本页用途与证据日期

本页汇总截至 2026-10-09 已有文档和代码检查所能支持的项目状态。它是状态索引，不替代 Active 产品决策、规格、ADR 或原始验证报告。除明确标注为 2026-10-09 的只读前端检查外，测试数字均来自 2026-09-26 的历史验证，不代表本日重跑。

## 项目定位与当前阶段

SkillShift Lab 的主线是研究 Agent 参与后职业任务、基础能力、人机责任边界和验证需求如何变化。SkillShift Studio 是实践与过程证据载体，不以通用模型或 Agent 能力超过 Codex、Cursor 等工具为目标。

当前产品方向是允许 AI 协同、让作业过程可见、可复核、可干预的职业项目工作流：教师设计并发布任务，学生在任务工作空间中与 Agent 协作、验证和提交，教师查看任务相关证据并反馈或要求补正。Python + CSV 是首个合成代表任务，不是产品的永久边界。

当前处于 R0 / R0.5 合成产品原型和证据边界整理阶段。已有控制面、教师/学生 Web 原型与一套 React Web 前端源码；尚无证据支持“产品已验收”或“Golden Path 已通过”。

## 资产与验证状态

| 领域 | 当前可确认状态 | 证据与限制 |
| --- | --- | --- |
| 流程控制面 | 教师创建/发布、学生工作区、提交、教师复核/补正等合成路径已有本机实现和有限浏览器验证。 | 最后记录的完整回归在 2026-09-26：Python 213 项（212 通过、1 跳过）、Node 43/43、Workspace API 39/39、WSGI 11/11、前端静态 48/48。唯一跳过为 Windows 符号链接创建权限不可用；这不是安全通过证据。详情见 [`CURRENT_STATE.md`](CURRENT_STATE.md) 和 [`控制面滚动报告`](../artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_P3_TASK_SWITCH_AND_REVIEW_ISOLATION_REPORT_2026-09-26.md)。 |
| 既有 HTML 页面 | `apps/teacher-web/`、`apps/student-web/` 和 `apps/agent-first/web/` 是不同用途的合成原型/Harness。 | 有不同范围的静态、API、WSGI 和 loopback 浏览器证据；不应合并称为同一套已验收产品。 |
| React Web 前端 | `apps/studio-web/` 有 React 19、TypeScript、Vite 工程；代码包含学生和教师路由、API DTO 校验与本机合成 API 调用。 | 2026-10-09 交接是源码只读检查；未运行 `build`、`lint`、服务或浏览器完整流程。不能声称该工程可启动或通过视觉/交互验收。详情见 `HANDOFF_STUDIO_WEB_FRONTEND_CONTINUATION_2026-10-09.md`。 |
| UI 设计资产 | `skillshift-studio-ui/` 有四张 HTML 设计稿、设计 token 和静态质量报告。 | 设计校验报告只覆盖相应设计文件，不是 React 页面验收或用户验收。 |
| 本机 Workspace API | React Vite 配置把 `/api` 代理至 `127.0.0.1:8000`；演示服务为 loopback-only、进程内存、固定合成身份/数据。 | 服务停止后数据清空；演示角色不是认证。已有旧页面与 API 的验证不自动覆盖 React 页面。 |
| Agent、模型与验证 | 已有确定性/合成引导路径；当前 React 前端未证明接入真实模型或学生可触发的确定性 Verifier。 | 不得把合成回复、静态输出或模拟验证称为真实 Agent 能力或验证结果。 |
| 代码执行 | React 工作区与任务 DTO 明确要求 `execution_enabled === false`；Foundation Spike 是独立安全研究切片。 | 未通过安全 Gate 前，不运行学生或外来项目；现有 ECS/Provider 不是可用沙箱。 |
| 身份、持久化、用户与部署 | 本轮材料未证明真实身份认证、生产持久化、真实学生使用、学校试点或部署。 | 产品价值、教师低负担、学习效果和研究结论仍未验证。 |

## 决策层级与未决事项

- 以 `product/R0_PRODUCT_REPOSITIONING_DECISION.md`、Active R0 产品/技术/质量规格和已接受 ADR 为准。
- V3.0 总纲是 Draft；与重定位决策冲突处不能覆盖 Active 决策。
- 桌面 Studio/本机节点与浏览器工作空间/远端执行服务的长期形态仍未决定。现有 React Web 工程只是已存在的 Web 实现，不等于长期产品形态已定为纯 Web。
- Active R0 要求使用平台固定协作模式；个别交接材料提出逐任务权限配置，但尚无新决策。当前原型保留固定模式，不新增权限编排。
- Task-level Verifier、Transfer 闭环、真实 Agent、真实身份、持久化、真实用户验证和生产部署均未由当前证据闭合。

## 建议的下一步（不代表已获授权执行）

1. 先建立可重复的本机演示基线：分别核对服务启动、React build/lint 和浏览器关键流程；记录失败、空状态、补正和窄屏证据。
2. 将 React Web 当前路由、实际 API 接线和合成边界与四张设计稿及 Active DTO/工作流逐项核对，再选一个有规格和验收条件的小任务。
3. 在产品决策未更新前，不新增真实代码执行、真实模型、任意 Agent 权限、真实学生数据、生产身份/持久化或部署。
4. 对研究材料保持保留和暂停扩展；研究结论须由独立、授权、可追溯的证据产生。

## Git 工作区快照

本次整理开始前（2026-10-09）检查到分支 `codex/r0-teacher-task-authoring`、HEAD `c5d6081`，11 项已跟踪状态项、118 条未跟踪路径项。Git 显示两份历史 Word 在 `wenben/` 根目录的旧路径删除；文件实际位于未跟踪的 `wenben/项目计划书_源文件归档/`，属于尚未暂存识别的移动。工作区还包含前端、规格、测试、Artifact 和交接文档等大量未跟踪资产。未发现配置的 Git remote 或当前分支 upstream。上述状态是现场快照；所有现存修改和未跟踪材料均须视为用户资产并在后续操作前重新核对。
