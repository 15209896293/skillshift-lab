# SkillShift Studio R0 技术规范

## 状态与边界

- 状态：**Active**（2026-09-24）。作为 Foundation Spike 的技术基线；其中标记 `Proposed` 的技术选择只可在 Spike 中验证，不能被描述为生产能力或真实学生试用前提。
- 上游：`../product/REQUIREMENTS_SPEC.md`、`../product/R0_PRODUCT_REPOSITIONING_DECISION.md`、`../product/R0_RESEARCH_TASK_EVIDENCE_CONTRACT.md`。
- 非目标：生产多租户 SaaS、任意不可信代码沙箱、全功能 IDE、全桌面监控、完整 LMS、正式研究数据平台。

## 1. R0 架构形态

R0 采用 API-first 的模块化服务与受限本机 Node，不是单一 Web 客户端。教师/导师通过 Web 端处理任务与复核；学生桌面 Studio / Agent Node 在本机绑定 Workspace 内运行基础 Agent 和 Python；服务端保存任务、提交、最小事件与允许同步的 Artifact 元数据。

```text
Teacher Web → Platform API → Student Studio / Agent Node → Bound local Workspace
```

Node 不获得宿主机完全控制权。浏览器不直接执行本机命令；服务端不将模型密钥、任意命令或不受限路径下发到 Node。

## 2. 技术选择与状态

| 范围 | 方向 | 状态 | 约束 |
| --- | --- | --- | --- |
| 教师 Web | Next.js、React、TypeScript | 选定方向 | 任务、复核、反馈与管理；不执行学生本机命令。 |
| 平台 API | Python、FastAPI、Pydantic | 选定方向 | 身份、状态、策略、同步和服务端边界。 |
| 业务数据 | PostgreSQL、SQLAlchemy、Alembic | 选定方向 | 查询状态、事件索引和迁移；不以聊天文本保存状态。 |
| 学生 Studio / Node | Tauri、Electron 或等价受限本机节点 | Proposed | 技术、安装更新、设备绑定与离线恢复由 ADR-001/Spike 决定。 |
| 本机 Workspace | 非 Docker 的 LocalRestrictedProcessProvider | Proposed | 独立根目录、非管理员身份、allowlist 与资源限制。 |
| Agent Runtime | AgentRuntimeAdapter | 选定接口 | Spike 可用确定性测试 Adapter，不声称实际 LLM 能力。 |
| 模型 | 服务端 ModelProviderAdapter | Proposed | Node 不保存 API Key；供应商、隐私、成本和可用性待确认。 |
| Artifact | 最小提交包 + 服务端元数据 | 选定原则 | 原始本机 Workspace 默认不整体上传；副本和保留由 ADR-003 决定。 |
| Docker | 不使用 | 已确认 | 不以恢复 Docker 作为 R0 前提。 |

## 3. 模块与职责

| 模块 | 职责 |
| --- | --- |
| Identity / Invitation | 最小教师、学生、Node 会话与受控任务加入；不接入完整教务。 |
| Assignment | 模板、材料、协作模式、人类责任、验证器版本和状态。 |
| Student Studio / Node | Workspace 绑定、任务同步、Agent 控制、事件缓冲和提交包生成。 |
| Workspace Provider | 路径、受限进程、命令策略、资源/网络策略与停止语义。 |
| Agent Runtime Adapter | 将 Agent 计划/工具动作映射到允许的 Workspace 工具。 |
| Submission / Artifact | Manifest、哈希、验证结果、允许的 Artifact 副本与同步状态。 |
| Review | 可解释信号、教师动作、学生说明/补正和环境问题。 |
| Event Registry | append-only 事件、schema 版本、序列、来源和审计索引。 |

## 4. Node 与 Workspace Provider 契约

最小操作：注册 Node、绑定 Workspace、启动/暂停/停止/接管 Run、读写允许路径、在允许命令范围内执行、构造提交包、同步事件和 Manifest。

每项操作必须验证 Node 身份、任务、Workspace、协作模式和工具策略。路径在 Node 内二次规范化，且结果必须仍处于绑定根目录；绝对路径、路径穿越、符号链接绕过、其他 Workspace、私人目录和未批准环境变量必须拒绝。

`LocalRestrictedProcessProvider` 是 R0 可行性假设，不是生产沙箱承诺。它至少需要非管理员身份、明确 cwd、超时、输出/文件大小限制、可追踪进程树、停止语义、允许命令列表、网络/依赖安装策略和错误记录。

Foundation Spike 未证明路径隔离、超时和停止可靠前，不运行任意外来项目、不安装任意依赖、不开放任意网络、不接收真实学生数据，也不将受限进程描述为安全沙箱。

## 5. Agent 工具、事件与状态

R0 工具仅限 `list_files`、`read_file`、`search_files`、`write_file`、`run_command`、`inspect_environment`、`stop_run`。每个调用关联任务、Workspace、Run、Node、模式、工具版本、输入摘要、结果、开始/结束时间和退出状态。

暂停、停止或接管必须改变 Run 状态并阻止后续工具调度。若停止无法确认，应显示 `STOP_UNCONFIRMED`，而不是显示已停止。

最小实体：User、Assignment、Enrollment、Node、Workspace、AgentRun、Submission、ArtifactManifestItem、ReviewAction、DomainEvent。可查询业务状态不得只存在于聊天记录或日志文本；事件为 append-only 事实，纠正通过新事件或明确状态迁移表达。

最小事件包括：`assignment.created`、`assignment.assigned`、`node.registered`、`workspace.bound`、`agent.run_created`、`agent.tool_called`、`runtime.command_finished`、`validator.finished`、`submission.package_created`、`submission.synced`、`submission.sync_failed`、`review.action_recorded`、`environment.issue_reported`。

Node 离线事件必须带单调序列、schema/Node 版本和同步状态；服务端拒绝无效身份、错误任务、重复或不连续批次，并把不能判定的情况标为待恢复而非伪造完整记录。

## 6. 提交包与同步

一次提交是可复核的 Manifest，不是本机全目录的远程镜像。至少包含任务/模板/验证器版本、Node/运行环境/Agent/模型引用、验证结果、事件引用、任务允许的 Artifact 清单及哈希、学生说明和同步状态。

Artifact 原始内容只有在任务契约允许且完成脱敏/权限检查后才可上传。教师界面只能引用已同步、可定位的内容；本机路径不能被视为教师可访问的证据。

具体加密、服务端位置、保留期限、退出/删除、导出审批和故障恢复由 ADR-003 在真实试用前确认。

## 7. API 与目录边界

建议 API 前缀为 `/api/v1`。所有写入关联当前身份、任务和 Workspace；Node 写入还关联注册会话。命令执行不是浏览器或任意 API 客户端的直通接口，只能由已授权 Node 内的受控 Run 调用。

目标目录为：`apps/teacher-web/`、`apps/student-studio/`、`apps/api/`、`packages/contracts/`、`execution/providers/`、`execution/agent-adapters/`、`execution/validators/`、`tests/{unit,integration,e2e,security}/`、`specs/R0-FOUNDATION-SPIKE/` 与 `artifacts/R0-FOUNDATION-SPIKE/`。本规范不授权提前创建这些源代码目录。

## 8. 必需 ADR 与工程门槛

实施 Foundation Spike 前至少维护：ADR-001（教师 Web、学生 Node、服务端职责）、ADR-002（受限 Workspace、命令/网络/依赖策略和停止语义）、ADR-003（提交包、Artifact 同步、数据最小化和保留/删除边界）。

模型供应商、真实学生数据、正式研究导出、学校身份接入和多设备支持不属于 Foundation Spike 的通过条件。
