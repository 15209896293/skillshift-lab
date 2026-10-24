# SkillShift Studio R0 技术规范

## 状态与效力

- 状态：**Active**（2026-09-24）；适用于 Agent-first R0 合成闭环。
- 上游：`../product/R0_AGENT_FIRST_DELIVERY_DECISION.md`、`../product/REQUIREMENTS_SPEC.md`、ADR-004。
- 边界：这里的技术选择是 Gate A 的最小实现基线；不代表生产部署、真实模型、真实学生、学校账号或本机代码执行已经获批。

## 1. 架构原则

R0 首先实现教学任务的 Agent 协作与复核状态，不实现通用电脑自动化。首条闭环必须简单、可回放、无外部网络依赖、可用合成数据验证，并允许日后替换 Agent 适配器。

```text
Teacher Task / Review UI
        ↓
Task + Submission + Review Application Service
        ↓
Versioned Agent Guidance Adapter
        ↓
Synthetic task fixtures and bounded local storage
```

## 2. 最小模块

| 模块 | Gate A 职责 | 明确不做 |
| --- | --- | --- |
| Teacher workflow | 创建固定任务、查看提交、记录反馈。 | 完整 LMS、成绩册、学校教务。 |
| Student workflow | 查看任务、Agent 对话、提交验证/解释/补正。 | 全桌面或浏览器监控。 |
| Task service | 维护任务模板、版本、角色和状态迁移。 | 多租户身份接入。 |
| Guidance adapter | 根据冻结任务给出确定性、可测试的引导。 | 真实模型调用、本机工具调用。 |
| Submission/review | 构造最小提交包、反馈与重新提交关系。 | 全目录上传、研究导出。 |
| Event ledger | 记录最小应用事件、版本与原因。 | 将日志解释为作弊或能力。 |

## 3. 核心契约

最小实体为：`Teacher`、`Student`、`TaskTemplate`、`Assignment`、`AgentInteraction`、`StudentResponse`、`Submission`、`ReviewAction`、`DomainEvent`。

所有写入须关联角色、任务、版本、时间和状态原因。事件为 append-only；状态变更可由事件回放。提交不能只引用 Agent 输出，必须包含学生任务关联响应。

最小状态机见 `../product/REQUIREMENTS_SPEC.md`。生产服务端/API、数据库和前端框架尚未选择；ADR-011 只为本机合成演示选择了 Python 标准库 JSON API 与无构建静态页面，用于验证交互契约，不能外推为生产技术选型。Gate A 可以在本地、无网络、可复现的实现中验证这些契约。

## 4. Agent 适配器

Gate A 定义一个最小接口：输入为冻结任务上下文和学生问题，输出为任务内引导及适配器版本。默认实现必须是确定性模拟，不读取本机文件、环境变量、凭据或网络。

OpenAI 路线（ADR-005）已被项目负责人否决。ADR-006 已确认 Gate B 的国产多模型网关边界：学生不持有或配置 Key；学校统一模型档位，教师可选 BYOK 只能通过未来服务端凭据引用实现。当前本地实现仍只保留可替换的 Guidance Adapter、档案白名单、失败关闭与确定性降级契约，不含网络或密钥。真实调用前仍须在受控服务端决定供应商、数据保留、成本、身份/租户、凭据保管、预算与审计策略；模型密钥绝不放入学生客户端。

ADR-007 已选择 DeepSeek 为首个**合成探针**供应商，并将 `deepseek-flash`、关闭思考、600 Token 上限、无工具/无联网搜索固定为本地请求契约。该选择不授权真实请求；学校统一凭据、实际价格、数据保留和运行时授权仍是后续 Gate B 前置。

## 5. 数据与安全边界

- 仅使用合成身份和合成任务；不连接现有 ECS，不部署。
- 不使用用户文件、密码、私钥、AccessKey、模型 Key 或真实学生数据。
- 不存储全量对话以外的桌面/浏览/其他应用信息；只保留闭环需要的最小字段。
- 任何教师复核理由必须显示事实、规则和不可观察边界，不能是隐藏评分。

## 6. 延后能力：本机 Code Workspace

`apps/student-studio/` 与 `execution/providers/` 的 Foundation Spike 是后续 Evidence Adapter 研究。将来若 Agent 获得文件读写、代码运行、子进程、依赖或网络能力，必须先以独立 ADR/规格定义权限和停止语义，并关闭相关路径、符号链接、进程树和网络安全证据。

Gate A 不调用这些 Provider，也不将其 PARTIAL 结果当作安全或产品通过。

## 7. 验证顺序

1. schema / 静态检查；
2. 状态机、权限与适配器单元测试；
3. 任务—提交—复核—补正集成测试；
4. 四个冻结案例的有界演示与 Artifact；
5. 文档、事件、提交包和测试之间的一致性审阅。

## 8. 2026-09-25 项目型 Agent 工作空间范围修订

项目负责人已确认教师 Web → 学生项目工作空间 → 后端纵向集成的产品顺序，产品职责见 `../product/R0_PROJECT_AGENT_WORKSPACE_DECISION.md` 与 `../../specs/R0-PROJECT-AGENT-WORKSPACE/README.md`。教师端和学生端必须是独立角色工作空间；共享 Task/Assignment、版本、会话、Agent Turn/Proposed Action、Artifact Reference、Evidence Event、Submission、Review Action 和 Remediation 等最小数据/API 契约需在实现集成前定稿。

学生工作空间目标可包含项目上下文、代码文本编辑、Agent 建议/差异检查和学生确认/拒绝/接管。原 Gate A 的确定性 Harness 不提供真实 LLM 或项目工作区能力。任何代码运行必须由与控制面隔离的独立执行 Provider 提供并通过专门安全 Gate；当前执行位置和 Provider 未决定，现有 ECS 只作为控制面候选，绝不能运行学生代码。真实模型、身份、持久生产数据和部署仍受 Gate B / ADR-013 限制。
