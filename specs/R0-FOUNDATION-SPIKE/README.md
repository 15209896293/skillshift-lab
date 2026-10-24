# R0-FOUNDATION-SPIKE：受限本机 Workspace 基础验证

> 2026-09-24 状态更新：本 Spike 的结果仍为 **PARTIAL**，且在未来引入本机 Code Workspace 或自动代码执行前仍是相关安全门槛。根据 `docs/product/R0_AGENT_FIRST_DELIVERY_DECISION.md` 与 ADR-004，它不再阻塞首条无本机自动执行的 Agent-first 教学闭环；不得据此把本 Spike 改称 PASS、Verified 或安全沙箱。

## Task ID 与类型

- Task ID：R0-FOUNDATION-SPIKE-001
- 类型：DEV_OS / 工程 Spike
- 状态：**Implemented / PARTIAL（2026-09-24；合成、本机、非生产范围）**。FS-01/03/07/08 有受限 PASS 证据；FS-02/05/06 为 PARTIAL；FS-04 为 FAIL。不得表述为安全沙箱或可用于学生代码。

## 1. 目标

在不使用 Docker、没有真实学生数据、没有真实模型密钥和没有教师 Web 功能的前提下，验证学生桌面 Studio / Agent Node 能否安全地完成最小本机 Workspace 生命周期：绑定合成 Python 项目、受限读写、执行允许命令、停止进程、生成事件与提交包 Manifest。

本 Spike 验证本机基础，不验证学习效果、教师需求、正式课堂可用性、任意不可信代码隔离或外部 AI 管理。

## 2. 上游与允许范围

必须先读：

1. `../../AGENTS.md`
2. `../../docs/product/REQUIREMENTS_SPEC.md`
3. `../../docs/architecture/TECHNICAL_SPEC.md`
4. `../../docs/quality/QUALITY_SPEC.md`
5. `../../docs/adr/ADR-001-hybrid-web-node-topology.md`
6. `../../docs/adr/ADR-002-local-restricted-workspace-boundary.md`
7. `../../docs/adr/ADR-003-submission-package-and-data-boundary.md`

允许范围：只建立 `apps/student-studio/`、`execution/providers/`、`execution/agent-adapters/`、`execution/validators/`、`packages/contracts/`、`tests/` 与 `artifacts/R0-FOUNDATION-SPIKE/` 中实现本 Spike 必需的最小内容。

禁止范围：教师 Web、正式 API/账号体系、模型供应商接入、真实 API Key、真实学生数据、任意依赖安装、任意网络、任意项目导入、云部署、完整 Artifact 上传、研究导出、评分与作弊判断。

## 3. 合成任务与人类责任

使用项目负责人拥有的、冻结版本的合成 Python 小项目。任务必须包含：可复现的起始故障或明确交付要求、固定运行/验证命令、允许写入的文件、预期 Artifact 和任务版本。

Spike 可使用确定性 `ScriptedAgentRuntimeAdapter` 或人工触发的受控工具调用来验证 Agent 生命周期；它不能被描述为已接入真实 LLM Agent。

人类责任最小形态：操作者在一次受控修改后运行验证命令，并提交一条与运行结果对应的验证说明。该说明只验证提交流程，不能作为学生理解证明。

## 4. 最小实现能力

1. Node 在配置根目录下创建或绑定一个 Workspace，并拒绝根目录外路径。
2. Provider 只允许固定的读、写、列举、搜索和验证命令；默认拒绝网络、依赖安装和其他 Shell 命令。
3. 每个 Run 有唯一 ID、状态、超时、输出上限和可追踪进程树。
4. 操作者可暂停、停止或接管；停止后不再调度后续工具。不能确认停止时显示 `STOP_UNCONFIRMED`。
5. 每项工具调用写入 append-only 事件，至少含 schema、序列、时间、Workspace、Run、动作、结果和版本。
6. 验证结束后生成最小 Manifest：任务/验证器/Node/运行环境/Adapter 版本、验证结果、Artifact 路径与哈希、事件引用、同步状态和验证说明。
7. Spike 可把 Manifest 写入本地 `artifacts/R0-FOUNDATION-SPIKE/`；不实现服务端同步，但必须把同步状态标为 `NOT_IMPLEMENTED`，不得伪称已上传。

## 5. 验收标准

| ID | 条件 | 验证证据 |
| --- | --- | --- |
| FS-01 | Workspace 创建/绑定仅位于指定根目录。 | 路径单元测试。 |
| FS-02 | `..`、绝对路径、符号链接和其他 Workspace 越界被拒绝并记录。 | 安全负向测试。 |
| FS-03 | 固定合成任务能通过允许命令完成一次验证。 | 集成测试、运行输出和 Artifact 哈希。 |
| FS-04 | 未允许命令、依赖安装、网络请求和超时命令被拒绝或安全停止。 | 策略/超时负向测试。 |
| FS-05 | 暂停、停止、接管和停止无法确认均产生正确状态与事件。 | 状态机、进程树和失败路径测试。 |
| FS-06 | 事件序列 append-only、可回放且带版本；重复/乱序事件不会被静默当作完整事实。 | 事件单元测试。 |
| FS-07 | 生成的 Manifest 可关联版本、验证结果、Artifact 哈希、事件引用和本地同步状态。 | Manifest Schema 测试与审阅。 |
| FS-08 | 不含真实学生数据、模型密钥、私人文件或完整本机目录。 | 数据/路径审计。 |

## 6. 失败与停止条件

任一条件出现即不扩大本机代码执行路线或声称运行环境安全：路径无法可靠限制；停止无法可靠管理且无诚实状态；命令策略可被绕过；Manifest 无法复核；日志含敏感内容；所需本机权限在目标环境不可获得。该停止条件不阻止经 ADR-004 单独定义的 Agent-first 教师/学生 Web 路径；该路径不得调用本 Spike 的本机执行 Provider。真实模型、学生数据和部署仍受其各自 ADR/PCP Gate 约束。

失败时保存最小复现、测试输出、环境版本与限制说明至 `artifacts/R0-FOUNDATION-SPIKE/`，并更新 ADR-002；不得靠忽略失败继续扩展。

## 7. 完成后允许的下一步

只有 FS-01 至 FS-08 全部有客观 PASS 证据，才可提出新的、单独授权的本机 Code Workspace / 代码执行集成规格。该后续规格可讨论代码 Workspace、受限 Provider、执行状态、停止/接管和执行证据同步。Agent-first 教师任务—学生 Agent 协作—提交—复核—补正闭环属于独立产品路线，已由 ADR-004 和 `specs/R0-AGENT-FIRST-VERTICAL-SLICE/README.md` 规定，不以本 Spike 通过为前置；但它不能启用本机代码执行。
