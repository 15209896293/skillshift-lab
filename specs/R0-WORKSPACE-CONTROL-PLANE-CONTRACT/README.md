# R0 项目工作区控制面 API / 领域契约

- Task ID：`R0-WORKSPACE-CONTROL-PLANE-CONTRACT-001`
- 类型：ARCHITECTURE / API CONTRACT
- 状态：**PROPOSED for local synthetic integration**；不是生产 API、身份或数据保留决策。
- Gate：P3 契约准备及代码级 DTO 接线已完成；HTTP/浏览器运行与视觉验证仍未通过，保持 Proposed / PARTIAL。
- 上游：`docs/product/R0_PROJECT_AGENT_WORKSPACE_DECISION.md`、`specs/R0-PROJECT-AGENT-WORKSPACE/README.md`、`specs/R0-TEACHER-WORKSPACE/README.md`、`specs/R0-STUDENT-WORKSPACE/README.md`、ADR-006 至 ADR-013。

## 1. 本任务的边界

目标是把分开的教师 Web 和学生编码工作区连到一个只处理**固定合成任务、状态与有界提交快照**的本机 API。服务不访问 ECS、不出网、不调用模型、不保存真实用户数据、不访问主机文件系统、不运行代码。

本契约沿用 `apps/agent-first/agent_first/domain.py` 中已验证的状态/角色分离原则，但不是对旧 Gate A API 的生产化。旧端点使用请求体中的 `actor_id`，只适用于固定演示；新端点不得把这个字段视作身份认证。

## 2. 合同约定

- Base path：`/api/v1`；JSON UTF-8；字段为 `snake_case`；每个顶层 JSON 请求/响应对象携带 `schema_version`，`data` 中的领域 DTO 由该 API 版本下的 JSON Schema 描述。
- 身份：服务端从认证上下文解析 actor 和角色；业务请求体不得指定 `actor_id`、角色、模型、Provider、密钥、任意执行权限或调用 URL。当前本机合成适配器可在测试夹具中注入固定 `teacher-demo` / `student-demo`，不可部署或对真实用户开放。
- 权限：教师只能读/改其有权管理的任务和复核该任务提交；学生只能读被指派已发布任务、操作自己的工作区和提交；角色/任务越权默认拒绝。生产身份/租户授权仍未决定。
- 请求关联：每个本机合成请求生成不透明 `request_id`；写操作的 EvidenceEvent 记录触发它的 request_id。幂等回放保持业务回执不变，但回放响应使用本次 request_id；不能把演示 ID 生成方式视作生产标准。
- 写入：每个有副作用的请求都带 `Idempotency-Key`。同 key + 同规范化请求回放相同业务结果；同 key + 不同内容返回 `409 idempotency_conflict`。状态更新另需 `If-Match` 修订号；客户端不提供事件序号。
- 版本：已发布任务版本不可原位改写；编辑产生新版本。学生 Workspace 固定指向发布时的任务版本。重提增加 Submission 版本，不覆盖历史。
- 事件：服务端分配单调 `sequence` 和 `event_id`；仅读取按 `after_sequence` 游标分页，单页最多 50 项。本机合成适配器最多暂留每 Workspace 256 项，旧游标返回 `409 cursor_expired`；这些数量不是生产留存期决策。仅允许列表中的操作事实。禁止把缺失、频率、相似度或 Agent 参与转成能力/作弊/努力结论。
- 默认实现：Provider 为 `scripted-demo`，响应恒明确标记固定演示。不能由客户端选择 Provider 或启用工具。无 `/run`、Shell、文件系统、包安装、浏览器或联网搜索端点。
- 测试路由：当前 `WorkspaceApi.handle` 仅在内存调用中根据 `/api/v1/demo/teacher/...` / `/api/v1/demo/student/...` 注入固定合成角色；这不是身份认证。正式集成前须由仅回环、仅演示的 HTTP/WSGI 适配器承接，且该适配器本身不得被部署。
- 存储：契约测试用临时 SQLite / 显式临时路径；旧 SQLite 实现只覆盖 synthetic Manifest 与预算回执，不是完整领域存储或生产数据库选型。默认禁止真实持久化。
- 传输内容：学生提交时可向本机合成 API 发送所选 allowlist 文件的 UTF-8 文本快照，以便教师查看具体提交内容。仅允许 `main.py`、`orders.csv`、`README.md`；单文件最多 8,192 UTF-8 字节，单次提交合计最多 12,288 字节，请求体仍受 16 KiB 上限约束。服务仅暂存进程内提交快照并计算字节数/SHA-256；不访问磁盘路径、不执行文件、不写日志，重启后清空。此项只覆盖本机合成内容，不是对真实文件上传、生产留存、访问审计或删除期限的决定；生产自由文本保留期限仍 UNKNOWN。

### 通用响应

成功：

```json
{
  "schema_version": "skillshift-api/v1",
  "request_id": "req-demo-opaque",
  "data": {},
  "revision": 3
}
```

错误：

```json
{
  "schema_version": "skillshift-api/v1",
  "request_id": "req-demo-opaque",
  "error": {
    "code": "state_conflict",
    "message": "该提交状态已变化，请刷新后再试。",
    "retryable": false
  }
}
```

不得在错误中回显密钥、原始提示全文、文件内容、文件系统路径或其他未过滤自由文本。候选 HTTP 码：`400` 字段/schema 错误，`401` 未认证，`403` 越权，`404` 不存在/不可见（防枚举），`409` 修订/状态/幂等冲突，`413` 请求超限，`422` 字段语义错误，`429` 有界重试限制，`500` 安全通用错误。

## 3. 最小领域对象

| 对象 | 最小字段与约束 |
| --- | --- |
| Assignment | `id`, `version`, `state` (`DRAFT` / `PUBLISHED` / `ARCHIVED`), `title`, `goal`, `starter_project_id`, `student_responsibility`, `submission_requirements[]`, `collaboration_mode` (`QA_ONLY` / `PROPOSE_WITH_STUDENT_CONFIRMATION`), `execution_enabled=false`, `created_revision`。文本长度沿用 `domain.py` 中 UTF-8 字节上限；项目清单从服务器固定 allowlist 选择。 |
| WorkspaceSession | `id`, `assignment_id`, `assignment_version`, `student_actor_ref`（服务端身份引用，非姓名/学号）, `state`, `revision`, `last_event_sequence`。一任务可有多个未来学生工作区，但本机原型只用一个合成学生；同一学生最多一个 `IN_PROGRESS` 工作区，允许 `PAUSED` 后切换。 |
| AgentTurn | `id`, `workspace_id`, `request_kind`, `provider_mode="scripted-demo"`, `response_text`, `availability`, `created_event_sequence`。学生原文仅用于当次处理；非经独立批准不持久化完整聊天。 |
| ProposedAction | `id`, `workspace_id`, `kind="FILE_PATCH_PREVIEW"`, `target_artifact_ref`, bounded `diff`, `status` (`PROPOSED` / `ACCEPTED` / `REJECTED` / `STUDENT_TAKEOVER`), `decision_event_sequence`。只提供预览/页面编辑，不写服务端文件、不执行。 |
| ArtifactReference | `id`, `workspace_id`, `logical_name`（只接受 allowlist 内 basename）, `media_type`, `size_bytes`, `sha256`, `source` (`FIXED_SYNTHETIC` / `CLIENT_DECLARED_SYNTHETIC`)。不存任意本机路径；当前不接受真实文件上传。 |
| ArtifactSnapshot | `logical_name`, `media_type`, `size_bytes`, `sha256`, bounded `content`。仅来自本机合成提交请求，文件名必须与引用清单完全对应；内容存于当前进程内，不能指向主机路径或触发执行。 |
| EvidenceEvent | `event_id`, server-assigned `sequence`, `schema_version`, `workspace_id`, `actor_role`, `event_type`, `resource_ref`, `occurred_at`（服务器时间）, `request_id`。不含完整聊天、键盘/粘贴遥测或未批准自由文本。 |
| Submission | `id`, `workspace_id`, `assignment_version`, `version`, `artifact_refs[]`, `artifact_snapshots[]`, `student_explanation`, `state` (`SUBMITTED` / `FEEDBACK_REQUIRED` / `ACCEPTED`), `created_event_sequence`。不自动评分。 |
| ReviewAction | `id`, `submission_id`, `submission_version`, `kind` (`ACKNOWLEDGE` / `REQUEST_EXPLANATION` / `REQUEST_EVIDENCE` / `REQUEST_REMEDIATION` / `ENVIRONMENT_ISSUE`), `reason`, `created_event_sequence`。所有动作含至少 8 个非空白字符的可理解理由；认可也不能省略。 |
| Remediation | `id`, `review_action_id`, `submission_id`, `requested_action`, `reason`, `state` (`OPEN` / `RESPONDED` / `CLOSED`), `response_submission_id`。`reason` 复用教师复核动作的具体要求，供学生查看；补正通过新 Submission 版本完成。 |

`student_actor_ref`、访问范围、用户账户与生产 tenant 的具体方案仍为 UNKNOWN，不在此任务中选择实现。

当前本机合成 API 的实际请求与响应 wire DTO 由同目录 `workspace-api-v1.schema.json` 严格描述，所有写请求必须携带 `schema_version=skillshift-api/v1`，未知字段默认拒绝；它不自动等于上表的目标领域对象或生产版本。Workspace 初始固定 ArtifactReference 仍标记 `integrity_status=NOT_COMPUTED`；提交快照另含受限文本、UTF-8 字节数和服务器计算 SHA-256。JSON Schema `maxLength` 按字符长度，UTF-8 字节上限由 API 代码和单元测试执行。Schema 测试依赖 `requirements-test.txt` 中 test-only 的 `jsonschema`，不进入产品运行时。

当前 Schema 同时定义了 API `data` 响应容器（任务目录、发布、复核队列、开始工作、Agent Turn、建议决策、提交、复核动作、补正列表及健康状态），并由 `test_workspace_json_schema.py` 对实际 API 响应逐项校验；查询工作区/任务与事件分页直接校验其 DTO。`SuccessEnvelope.data` 通过 `ResponseData` 限定为当前所有已声明的 wire DTO 联合类型，拒绝未声明对象；Schema 仍不能依据 URL 自动绑定到唯一 `data` 子类型，因此契约测试继续对真实路由逐项校验预期 DTO。QA_ONLY Agent Turn 可不含 `proposed_action`。

## 4. 端点契约（候选）

所有读请求仍执行资源级授权。所有写请求要求 `Idempotency-Key`，状态突变要求 `If-Match`，返回统一 envelope。

| 方法与路径 | 角色 | 作用/关键约束 |
| --- | --- | --- |
| `GET /health` | system | 只报本机合成服务状态，不泄露环境、路径、密钥或服务配置。 |
| `POST /assignments` | teacher | 创建 `DRAFT`；只接受声明的任务文本、固定模板 ID 和协作枚举。 |
| `GET /assignments` | teacher | 返回当前 actor 可管理的任务摘要。 |
| `GET /assignments/{id}` | teacher / assigned student | 学生仅能读自己获派且已发布的版本。 |
| `POST /assignments/{id}/publish` | teacher | DRAFT → PUBLISHED；冻结该版本并创建绑定版本的 WorkspaceSession。 |
| `GET /workspaces/{id}` | assigned student / authorized teacher | 学生读任务、固定文件引用和自己工作区；教师读任务要求与必要提交状态，不读任意私有数据。 |
| `POST /workspaces/{id}/start` | assigned student | `ASSIGNED` → `IN_PROGRESS`；必须满足当前修订号。 |
| `POST /workspaces/{id}/pause` | assigned student | `IN_PROGRESS` → `PAUSED`；必须满足当前修订号。`start` 可恢复 `PAUSED`；若其它工作区仍 `IN_PROGRESS` 则返回 409，不隐式暂停或切换。 |
| `POST /workspaces/{id}/agent-turns` | assigned student | 返回有 `provider_mode=scripted-demo` 标记的固定合成答复；默认不持久化学生原始问题。 |
| `POST /workspaces/{id}/proposed-actions/{id}/decision` | assigned student | 只记录 ACCEPTED / REJECTED / STUDENT_TAKEOVER 决策事实；不可触发文件写入或代码运行。 |
| `POST /workspaces/{id}/submissions` | assigned student | 提交有界说明、allowlist Artifact Reference 与严格对应的合成文本快照；创建版本，不含评分字段。生产环境不得据此接受真实附件。 |
| `GET /workspaces/{id}/submissions/latest` | assigned student (Proposed local-synthetic extension) | 返回此已发布工作区当前最新完整 Submission，含该提交的文本快照；无提交时返回 `submission: null`。只读进程内存，不读取历史列表、不证明对应某次页面内未知请求，不向 teacher role 开放；教师仍使用 review-queue。 |
| `GET /assignments/{id}/review-queue` | teacher | 只返回当前可复核提交的最小字段，不含“风险分/作弊”摘要。 |
| `GET /assignments/{id}/review-history?after_sequence=n&limit=n` | teacher (Proposed local-synthetic extension) | 返回指定已发布任务现有 ReviewAction 元数据分页；1–50 项，不含提交快照/说明。只支持固定 teacher-demo 合成路由，不是正式教师授权。 |
| `POST /submissions/{id}/review-actions` | teacher | 必须命中当前 Submission 版本，所有动作理由至少 8 字；证据/补正动作创建 Remediation。 |
| `GET /workspaces/{id}/remediation` | assigned student / authorized teacher | 显示面向学生的具体补正请求与状态。 |
| `GET /workspaces/{id}/events?after_sequence=n` | resource-authorized actor | 返回严格递增的事件页；after 仅为读取游标，不是客户端可写序号。 |

`GET /workspaces/{id}/submissions/latest` 是本机合成契约新增的 Proposed 读取扩展，尚未成为 Accepted 产品/生产接口。它只允许固定 student-demo 路由读取其获派且已发布工作区中最新一条完整 Submission；不存在时返回明确的 `null`，未知或未发布工作区使用统一 `404 not_found`。该读取不改变修订号、事件或工作区状态，不返回历史列表，也不能将刷新后读到的最新提交关联为之前某次丢失回执的成功确认。固定 demo 角色不构成真实身份或生产授权证据。

`GET /assignments/{id}/review-history` 是另一项本机合成 Proposed 扩展：固定 teacher-demo 仅能读取已发布任务的 ReviewAction 元数据，按服务端 `created_event_sequence` 游标分页（单页最多 50）；空历史返回空数组，未知/未发布/无工作区资源与 student-demo 请求统一 `404 not_found`，无效游标或页数返回参数错误。该 DTO 不包含 Submission 快照或学生说明，GET 不改变修订号或事件。它可让教师刷新后查看当前暂存的复核动作，但由于页面 attempt/幂等键在刷新后丢失，历史中某条 ACK 不能被说成确认了某次先前未知请求。固定 teacher-demo 不证明真实教师对任务的授权；复核理由数据只在当前进程内存。

提交后形成 `REVIEW_REQUIRED`；非认可 ReviewAction 形成 `FEEDBACK_REQUIRED` 与开放补正；学生响应创建下一版 Submission；教师 `ACKNOWLEDGE` 关闭该任务轮次。环境问题可以标记为待处理，不推断责任归属。

## 5. 限额与失败行为

- 每个 JSON 请求最大 16 KiB（与旧本机 API 的实验上限一致；实施前以跨组件测试锁定）。自由文本按 UTF-8 字节计数；提交快照单文件最多 8 KiB、合计最多 12 KiB；拒绝无效 UTF-8、NUL、未知文件名/字段、超长字段和未知枚举。
- 事件游标过旧时返回 `409 cursor_expired` 与“刷新工作区”提示，不静默跳过；`limit` 必须是 1–50 的单一整数。当前合成内存层每 Workspace 最多暂留 256 个事件；数据重启即清空，不能据此推出生产历史保留期限。未知提交回执不得允许重复提交形成两个版本，同幂等 key 重放原回执。
- 并发更新的 loser 收到 `409 stale_revision`，先刷新显示后由人决定是否重试；不得静默覆盖教师/学生正在编辑的数据。
- 每个成功的工作区状态写入必须产生新的服务端修订号；提交时读取到旧修订号的新请求必须以 `409 stale_revision` 拒绝。相同幂等键、相同请求的合法重放仍返回原业务回执，不重复产生事件或副作用。
- 同一工作区事件序号由服务端唯一递增；客户端时间只作显示输入，不决定事件顺序。
- 空队列、未提交、服务不可用、过期会话、冲突和未知派发均为显式 UI 状态。服务不可用不得合成“已发布/已提交”成功。
- 本机合成 API 在提交后暂存 allowlist 快照至服务进程内存，供教师复核；学生草稿仍暂留浏览器页面。重启后两者均清空。生产内容保存、删除期限、加密、跨设备恢复和真实审计访问均未决定。

## 6. 已知实现差距（集成前不得声称接口已具备）

1. `apps/agent-first/agent_first/local_web.py` 是 `/api/` 单版本临时 API，用请求体 `actor_id` 切换两个固定合成角色；不可用于生产身份或直接假定兼容 `/api/v1`。
2. `domain.py` 没有 Assignment 发布版本、项目文件引用、WorkspaceSession、Agent Turn/Proposed Action、Evidence Event、Evidence Request 或 Remediation 聚合对象。
3. 旧 ReviewKind 没有 `REQUEST_EVIDENCE`；旧 `ReviewAction` 和 `EducationWorkflow.review` 要求至少 8 字理由。独立教师 UI 现把所有复核动作映射为 API 枚举，并在调用前验证至少 8 个非空白字符；仍未做浏览器验收。
4. `workspace_api.py` 是纯内存测试 Router，由合成 API 测试和同目录严格 wire JSON Schema 测试覆盖；该 Schema 只锁定当前本机合成 wire 对象，不是完整领域目标或生产 DTO 版本。事件单页与每 Workspace 内存保留有界。`workspace_wsgi.py` 以直接 WSGI 调用适配 API，并按固定 allowlist 提供教师/学生页面静态资源；尚未启动 HTTP 服务，无持久化或正式认证/授权。适配器按 WSGI `REMOTE_ADDR` 拒绝非回环来源；部署/反向代理配置不受代码保证，因此该 demo 角色仍不能当安全边界，也不得部署。
5. Workspace 的固定 ArtifactReference 仍只含 allowlist 元数据并标记 `integrity_status=NOT_COMPUTED`。Submission 新增本机合成 ArtifactSnapshot 字节/哈希校验，但没有统一学生初始文件来源；候选 fixture、学生页内嵌文本与教师静态示例仍重复，不能视为唯一权威来源。
6. `control_plane_persistence.py` 只验证合成 Manifest 快照和预算预留；不得用其测试结论声称完整领域 API 已持久化。
7. 教师与学生静态原型已加入本机合成 API 的代码级调用和 DTO 映射，并通过 mock-fetch、静态 DOM 引用及直接 WSGI 纵向调用测试；客户端对页面消费的任务、工作区、提交快照、补正与事件读取 DTO 执行最小结构校验，并对教师队列快照重新计算 UTF-8 字节数与 SHA-256。教师复核写入若回执不确定，只在工作区状态关闭或读回到同一提交、同一动作及同一理由的开放补正时显示读回确认；读取仍不确定时保留未知/不可用状态。学生对同一提议决定的未知回执使用相同幂等键重试，处理中锁住冲突决定按钮，未知时仅允许重试原动作。这不等于对每个字段运行完整 JSON Schema 校验，也不等于已运行 HTTP 服务或浏览器集成。固定 demo 角色不是权限会话，scripted-demo 不是真实 Agent，页面编辑仍只在浏览器内存。

## 7. 验收与停止

契约测试最少包含：每个 wire DTO 的 JSON Schema、UTF-8 字节上限；教师与学生矩阵越权拒绝；版本冻结/修订冲突；幂等相同请求回放、异文冲突；事件唯一顺序/断点分页/过期游标；固定 Agent 只能返回 scripted 标记；Proposed Action 的学生确认和拒绝；Artifact allowlist 与凭据扫描；提交版本和补正闭环；服务故障不伪造成功；前端当前状态读取和错误展示。API/schema/WSGI 测试覆盖代码级服务行为；前端 mock-fetch/静态测试覆盖当前 DTO 映射和错误状态，不覆盖真实浏览器请求、视觉或刷新运行效果。独立只读凭据指示器扫描已执行，范围、7 条合成测试样例命中及限制见 `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_CREDENTIAL_SCAN_REPORT_2026-09-25.md`；该自定义扫描不替代专用凭据扫描器，也不证明任意凭据不存在。

2026-09-25 本阶段执行边界：项目负责人明确要求先实现教师/学生与合成本机 API 的代码级 DTO 接线和错误测试；若无合规预览路径，只运行静态、单元和直接 WSGI 调用测试。因此本次完成了前端 `fetch` 客户端及页面调用代码，但没有启动 HTTP 服务或打开浏览器。浏览器/HTTP 运行验收仍是 P4 纵向闭环验证的前置条件；本次 P3 结果为 PARTIAL，不得声称端到端产品集成通过。出现真实用户/身份/数据、第三方模型/密钥/费用、数据生命周期选择、ECS/部署、上传真实附件或代码执行需求时，停止对应扩展并单独决策。ECS 仍仅控制面候选，绝不作为代码执行器。

2026-09-25 后续 P3 验证：`artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_FIXTURE_SNAPSHOT_INTEGRATION_REPORT_2026-09-25.md` 记录候选 Fixture 的三个文本文件经 `artifact_contents` 进入 API 快照并由教师队列读回时，逐文件文本、UTF-8 字节数和 SHA-256 对照通过。该测试不将 `CANDIDATE_CANONICAL_SOURCE` 提升为正式唯一来源，也不改变本规格的 Proposed 状态、内存暂存或非生产边界。

2026-09-25 WSGI 纵向回读验证：`artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_WSGI_VERTICAL_READBACK_REPORT_2026-09-25.md` 记录一条不启动服务的 WSGI callable 测试，顺序覆盖教师创建/发布、学生发现/开始、scripted-demo Agent 回合、学生拒绝 Proposed 文件修改、候选 fixture 文本快照提交、教师读取/要求补正、学生重提及 ACK；同时检查学生最新提交完整 DTO 回读、教师 ReviewAction 分页、跨角色 404、错误游标 400 与 `no-store`。该证据只说明 API/适配器代码路径可直接调用，不代表 loopback 网络绑定、HTTP 服务、浏览器、认证、持久化或生产集成。非字符串 `REMOTE_ADDR` 的类型错误现与无效 IP 一样显式返回 403；这只是适配器防御，不是对任意 WSGI 容器/反向代理的部署保证。

2026-09-25 教师创建/发布回执防伪成功校验：只读审计发现客户端对 2xx 回执的创建 DTO 检查过宽，发布 DTO 也未验证 Workspace 与 Assignment 归属。`apps/workspace-client.mjs` 现要求创建回执是完整 DRAFT Assignment（含任务、演示边界、无 Workspace）；发布回执要求完整 PUBLISHED Assignment 与 ASSIGNED Workspace DTO、一致的 Assignment ID/Workspace ID，并确认 `execution_enabled=false`。发现并修复了成功包络修订号应对应发布后的 Assignment revision，而非新 Workspace revision。Node 故障注入测试覆盖缺字段 CREATE 回执、错误关联 PUBLISH 回执、未确认状态及同幂等键/DTO/If-Match 重试；Node 34/34、WSGI 9/9、前端静态 14/14，完整 Python 172 项（171 PASS、1 SKIP）。真实 API 的校验拒绝/409 分支保持明确失败；WSGI stale publish 测试确认拒绝后仍是 DRAFT，只有显式以最新 revision 再请求才发布。代码级 DTO 防线只验证页面依赖字段和关键关系，不是通用完整 schema validator；浏览器/HTTP/P4 仍未运行，整体集成 PARTIAL。详情见 `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_TEACHER_CREATE_PUBLISH_RECEIPT_GUARDS_REPORT_2026-09-25.md`。

2026-09-25 学生最新提交读回竞态校正：独立只读审计发现初始化 GET 与提交成功后的 GET 并发时，旧全局单飞锁会静默丢弃后一次刷新，迟到的“空/旧提交”结果可能覆盖新提交状态。`apps/student-web/app.js` 现为每次回读分配递增请求代次，只允许最新发起的成功或失败结果写入独立状态区；读取不会改写编辑器或清除待确认提交。`apps/workspace-client.mjs` 对 latest data wrapper 采用准确字段集检查，拒绝 Schema 禁止的额外字段。静态源码测试覆盖成功和 catch 两条过期结果保护；客户端故障测试覆盖 `{submission:null, unexpected:true}`。Node 34/34、前端静态 14/14，完整 Python 172 项（171 PASS、1 SKIP），学生 JS 语法检查通过。该竞态修复有静态断言而没有 DOM/浏览器时序测试；HTTP/浏览器/P4 仍未运行，整体集成 PARTIAL。仅本机合成、进程内存、非生产；最新提交仍不是某次未知请求的精确回执。详见 `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_STUDENT_LATEST_READ_RACE_GUARD_REPORT_2026-09-25.md`。

2026-09-25 学生 Agent 协作失败状态补正：审计发现 REJECT/STUDENT_TAKEOVER 的未知回执没有保留精确提案、动作和修订号；可发起新 Agent Turn 覆盖全局 proposal ID，造成原动作无法安全重试。学生端现用 ProposalDecisionAttempt 固定这四项，未知时只开放同一动作重试，禁止新 Agent Turn 和提交入口。Node 客户端按原 route/body 复用 pending Idempotency-Key；三种决定都从 `data.workspace_revision` 更新本地版本，即使可选 envelope `revision` 缺失。另对 `availability=UNAVAILABLE` 显示明确无引导状态、保留问题输入、不插入成功回复/Toast。Node 35/35、前端静态 16/16、WSGI 9/9，Python 全量 174 项（173 PASS、1 SKIP）；JS 语法、Schema JSON、`git diff --check` 通过。此项无浏览器时序测试；静态断言和 mock-fetch 不证明真实运行时视觉。教师补正旧响应的 generation guards 已做源码检查，但动态 DOM 并发验证仍缺；之后仍按本机合成/P3 边界继续。整体集成 PARTIAL，固定 demo 角色非认证，API 进程内存，代码执行关闭。详情见 `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_STUDENT_COLLABORATION_ERROR_STATES_REPORT_2026-09-25.md`。

2026-09-25 后续 UI 失败状态校验：`artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_UI_WRITE_RETRY_GUARDS_REPORT_2026-09-25.md` 记录教师任务保存/发布及学生提交的请求中防重复触发；学生提交回执未知时保留原请求 DTO 和修订号，仅允许同内容幂等重试并冻结编辑。该结果由脚本语法、静态源码断言和客户端测试支持，没有浏览器运行证据。

2026-09-25 教师发布恢复扩展：`artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_TEACHER_CREATE_PUBLISH_RETRY_REPORT_2026-09-25.md` 记录教师未知 CREATE/PUBLISH 回执保留原 DTO、步骤与 assignment 上下文；PUBLISH 明确冲突先回读原任务，DRAFT 时更新 revision 并等待教师再次明确点击，不能重新创建草稿。状态机有静态源码分支断言和客户端 path/body/key/If-Match 故障注入；不含浏览器运行证据。刷新页面仍会丢失前端未决 attempt，生产持久恢复不在本机合成契约中。

2026-09-25 教师复核与学生写入错误恢复扩展：`artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_UI_ERROR_RECOVERY_REPORT_2026-09-25.md` 记录教师未知复核写入保留原动作/DTO/提交/版本并仅允许同请求重试；学生 Agent 问题与建议接受保持请求上下文，补正读取失败展示显式未知；教师刷新可读取所有已发布任务的补正记录，即使复核队列为空仍保留 OPEN/RESPONDED 历史，读取失败显示未知。客户端对 Agent、Workspace Start、Submission、ReviewAction 写回执增加页面关键字段和请求匹配校验。ACK 不再仅凭 Workspace `CLOSED` 状态确认，等待原幂等写入回放回执。Node 故障注入 26/26、前端静态状态测试 11/11、Workspace API 定向测试 29/29、完整 Python 回归 162 项（161 PASS、1 SKIP）。这些不是浏览器交互测试；HTTP/浏览器和 P4 视觉验证仍未完成。页面内待确认请求重载即丢，精确提交历史读取和教师复核历史读取尚未提供。

2026-09-25 学生最新提交 Proposed 回读扩展：`GET /workspaces/{id}/submissions/latest` 仅限本机固定 student-demo 的本人、已发布工作区；空工作区严格返回 `submission: null`，否则只返回完整最新 Submission 与快照，不返回历史列表。读取不改变 revision/event；teacher、未知工作区、owner 不符、未发布统一 not_found，教师仍走 review queue。Schema 与 API/客户端/页面静态测试锁定空值、版本、状态、快照、hash、权限和失败状态。学生刷新可查看 API 当前记录，但不能把它解释成确认某次先前未知回执。Node 客户端 30/30、前端静态状态 12/12、API 定向 31/31、Schema 定向 8/8、完整 Python 166 项（165 PASS、1 SKIP）。详细边界和当前文件哈希见 `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_LATEST_SUBMISSION_READBACK_REPORT_2026-09-25.md`。扩展仍是 Proposed、本机合成、内存暂存；HTTP/浏览器/P4 视觉 QA 未运行，整体集成仍 PARTIAL。

2026-09-25 教师 ReviewAction 历史 Proposed 扩展：`GET /assignments/{id}/review-history` 为固定 teacher-demo 的已发布任务读取动作元数据分页；页面可在 ACK 后回看记录，单页最多 50 条，response 不含提交快照/学生说明，统一资源隐藏错误、不改变 revision/events。教师界面显示空/失败/历史状态并支持翻页；未知写入尝试仍不被历史记录冒充回执，过期的队列/补正/历史请求被 generation guard 丢弃。Node 客户端 33/33、前端静态测试 14/14、API 定向 34/34、Schema 定向 8/8、完整 Python 回归 171 项（170 PASS、1 SKIP）。此扩展仍 Proposed；固定 teacher-demo 不验证真实教师归属授权，浏览器/HTTP/P4 未运行，整体集成仍 PARTIAL。详细证据和 SHA-256 见 `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_TEACHER_REVIEW_HISTORY_REPORT_2026-09-25.md`。

2026-09-25 幂等修订前置与纵向事件链校验：只读审计发现状态写入幂等指纹原先未包含 `If-Match`，同一 key/body 改用错误或过期修订号也会直接回放成功。`_mutate` 现将规范化 `If-Match` 纳入指纹，缺失或不同前置条件与原请求不同时返回 `409 idempotency_conflict`；完全相同的 key/body/If-Match 仍回放且不重复副作用。学生提交页面现优先从必需的 `data.workspace_revision` 更新本地 CAS 版本，包络 `revision` 缺省时也能推进。WSGI 闭环测试通过适配器精确重放和改变 If-Match 的冲突，并将八个状态事件逐一与回执 sequence、event_type、resource_ref 对照，验证严格递增唯一。Node 客户端 35/35，前端静态 17/17，WSGI 9/9，Workspace API 34/34；Python 全量 175 项（174 PASS、1 SKIP）。Schema JSON、JS 语法、Python 编译与 `git diff --check` 通过。浏览器/HTTP/P4 QA 仍未运行；整体仍 PARTIAL、本机合成、进程内存、非生产，固定 demo 角色非认证，代码执行关闭。详情见 `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_IDEMPOTENCY_REVISION_EVENT_GUARDS_REPORT_2026-09-25.md`。

2026-09-25 WSGI peer-address 回归：只读审计确认 `WorkspaceWsgiApp` 以 WSGI `REMOTE_ADDR` 判定 loopback，不读取 `HTTP_X_FORWARDED_FOR`；契约同时明确反向代理/部署配置不受代码保证。新增直接 callable 测试锁定 `::1` 回环放行、`2001:db8::1` 非回环拒绝，以及非回环 `REMOTE_ADDR` 携带伪造 `X-Forwarded-For: ::1` 仍拒绝。测试注释明确这不证明网络监听地址或反向代理部署安全。WSGI 10/10 PASS；Python 全量 176 项（175 PASS、1 SKIP）。仅本机合成、非生产；没有启动服务/端口或浏览器，P4 QA 仍未完成，整体保持 PARTIAL。详情见 `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_WSGI_PEER_ADDRESS_GUARD_REPORT_2026-09-25.md`。
