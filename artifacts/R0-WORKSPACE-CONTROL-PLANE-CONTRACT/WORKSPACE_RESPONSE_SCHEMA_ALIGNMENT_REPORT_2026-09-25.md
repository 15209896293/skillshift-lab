# R0 Workspace 响应 DTO Schema 对齐报告

## 状态

- Task ID：`R0-WORKSPACE-RESPONSE-SCHEMA-ALIGNMENT-001`
- Gate：P3 本机合成代码级响应 DTO 契约：**PASS**。
- 整体 Workspace 集成 Gate：**PARTIAL**；未启动 HTTP 服务、未做浏览器视觉 QA。
- 范围：严格定义并校验本机合成 API 的响应 `data` DTO 容器；非生产、非部署。

## 差距与处理

只读审计教师页和学生页的 `data` 消费点、API 路由返回值及 Schema 后，发现 Schema 已声明响应内部 DTO（如 Assignment、Workspace、Submission、ReviewAction），但 `SuccessEnvelope.data` 只有通用 object 约束，实际 API 的若干响应包装对象并未定义。这样测试无法防止 UI 消费形状与 API 返回容器漂移。

在既有 wire schema 中增加以下严格容器：`HealthData`、`AssignmentListData`、`AssignmentPublishData`、`ReviewQueueData`、`WorkspaceStartData`、`AgentTurnData`、`ProposedActionDecisionData`、`SubmissionData`、`ReviewActionData`、`RemediationListData`。现有 `Submission` 已包含 `workspace_id`，复核队列项复用此 DTO。`AgentTurnData.proposed_action` 保持可选，以支持 `QA_ONLY` 模式。

Schema 测试现在调用合成 API，逐一使用其实际响应检查目录、任务创建/读取、发布、工作区读取/开始、Agent Turn、建议决策、提交快照、教师复核队列/动作、补正和事件分页；纵向路径继续验证教师请求补正、学生第 2 版重提、补正转 RESPONDED、教师认可关闭及待复核队列清空。另有负例验证响应 DTO 拒绝额外路径字段，并直接调用 QA_ONLY 路径确认 Agent Turn 可省略建议对象。合同 README 说明了 Schema 的覆盖范围和限制。

同一轮错误状态复核又发现客户端会接受结构错误的 HTTP 2xx response。客户端现在对创建、发布、开始、Agent Turn、建议决定、提交和复核写操作验证最小回执字段/状态；成功 Envelope 的 `data` 也必须是非数组对象。Node 用例覆盖 malformed/状态不匹配回执，以及教师创建、发布、补正复核、认可和学生第二版重提。Python 静态页面测试现锁定两端关键调用链（教师创建/发布/复核队列/快照；学生任务发现/工作区读取/开始/Agent/提交/补正）；这只证明源代码接线关系，不是浏览器运行证据。运行时检查是最小防伪回执，不替代 API JSON Schema 的完整约束。

复核 409 错误映射发现 `state_conflict` 与 `cursor_expired` 原先落入通用校验拒绝提示。现在客户端将所有 HTTP 409 归类为冲突状态（`idempotency_conflict` 保留专用提示），Node 测试覆盖 stale submission、state conflict、过期 cursor 与幂等冲突，且确认服务端自由文本不会泄漏到提示。

由于 UI 对 4xx 校验拒绝显示 API `message`，又静态核对了 API 所有 `ApiFault` 生成点：消息使用固定文案或服务端有界页大小，不插入任务自由文本、学生说明、提交内容或主机路径。已有不允许 artifact 与过短说明的 API 测试现在额外断言响应不会回显路径/提交说明。

随后将 `SuccessEnvelope.data` 从通用 object 收紧为 `ResponseData` 的已声明 DTO 联合，并逐项用当前 API 路由的完整 success envelope 验证。负例锁定 `{}`、数组和未知对象均不合法。联合只约束当前 API 已声明的响应形状，不依据 URL 绑定唯一响应子类型；每条路由仍由契约测试校验具体 DTO。

## 修改文件

| 文件 | 原因 |
| --- | --- |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json` | 定义 API 响应 `data` 包装 DTO 和字段约束。 |
| `tests/test_workspace_json_schema.py` | 对实际 API 响应逐项校验 DTO，并覆盖严格字段与 QA_ONLY 可选字段。 |
| `tests/test_workspace_frontend_html.py` | 静态锁定教师/学生页面到 DTO 客户端的关键调用链。 |
| `tests/test_workspace_api.py` | 断言 API 校验错误不回显任意路径、文件内容或学生自由文本。 |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | 记录响应 Schema 覆盖及 `SuccessEnvelope.data` 通用类型的限制。 |
| `apps/workspace-client.mjs` | 拒绝 2xx 非对象 `data`，并核验会更新界面成功状态的写操作最小 DTO 回执。 |
| `tests/workspace-client.test.mjs` | 校验教师和学生各阶段写回执、malformed response、409 冲突分类及网络失败不成为成功回执。 |
| `README.md`、`docs/README.md` | 将项目入口中的过期回归计数同步为本轮可复核结果，并链接本 Artifact。 |
| `docs/CURRENT_STATE.md` | 追加本阶段当前状态和门禁边界。 |
| `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_RESPONSE_SCHEMA_ALIGNMENT_REPORT_2026-09-25.md` | 保存本任务可复核证据。 |

## 验证

- `python -m unittest discover -s tests -p test_workspace_json_schema.py -v`：7/7 PASS。
- `python -m unittest discover -s tests -p test_workspace_frontend_html.py -v`：3/3 PASS，含新增调用链断言。
- `python -m unittest discover -s tests -p test_workspace_api.py -v`：28/28 PASS，含错误消息不回显断言。
- `python -m unittest discover -s tests -v`：152 项，151 PASS、1 SKIP，最终复跑 48.262 秒。唯一跳过为 Windows 环境缺少创建符号链接权限；该跳过不构成符号链接安全通过证据。
- `node --test tests/workspace-client.test.mjs`：13/13 PASS。
- `node --check apps/workspace-client.mjs`、教师页与学生页脚本：通过。
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`：通过。
- `python -m py_compile apps/agent-first/agent_first/workspace_api.py tests/test_workspace_json_schema.py`：通过。
- `rg -n -C 1 "ApiFault\\(" apps/agent-first/agent_first/workspace_api.py`：逐项复核 API 错误消息拼接点；只含固定文案或服务端有界常量，无学生输入、快照内容或主机路径回显。
- `git diff --check`：通过。
- `README.md` 与 `docs/README.md` 的动态测试计数及 Artifact 相对链接已现场核对；没有改写历史 handoff。
- 首次误用 `python -m unittest tests.test_workspace_json_schema -v` 时，因 `tests` 不是 Python package 导致导入错误；改用上述 unittest discover 命令后定向测试通过。该导入错误与代码行为无关。

## 边界、风险与下一步

- `SuccessEnvelope.data` 已封闭为所有当前响应 DTO 的联合，但 JSON Schema 不根据 URL 自动选择对应子 Schema；测试按真实 endpoint 逐项校验，不应把“属于联合类型”误说成“该路由语义已被静态绑定”。
- 未做 HTTP 服务启动、浏览器网络请求或视觉检查；P4 未验证，整体 Gate 保持 PARTIAL。
- 固定演示角色不是认证；数据仍只在进程内存暂存，代码执行关闭，Foundation Spike 仍 PARTIAL。
- `orders-audit-v1` fixture 仍标记 `CANDIDATE_CANONICAL_SOURCE`，页面嵌入内容经测试与候选文件一致但不是唯一运行时来源；不在此任务自行接受其为长期 canonical 数据供应方案。边界与选项见 `WORKSPACE_FIXTURE_CANDIDATE_REPORT_2026-09-25.md`。
- P3 直接 API DTO 闭环已覆盖到第二版重提与关闭；HTTP/浏览器视觉 QA 仍未验证。继续审计静态/契约可验证的剩余差距；只有出现产品/数据/身份/部署等实质决策时才暂停。

## Git

- 分支：`codex/r0-teacher-task-authoring`。
- 修改只限上述 Schema、测试、客户端、合同、状态和本 Artifact；工作区其他既有未提交/未跟踪内容完整保留。
- 未提交、推送、部署或清理文件。
- Commit：`NONE`。
