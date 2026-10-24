# R0 Workspace 请求 DTO 版本字段对齐报告

## 状态

- Task ID：`R0-WORKSPACE-REQUEST-SCHEMA-ALIGNMENT-001`
- 本机合成 API 写请求 DTO / 严格 Schema 对齐：**PASS**。
- 整体 Workspace 集成 Gate：**PARTIAL**；P4 HTTP/浏览器请求与视觉验证仍未执行。
- 范围：固定演示角色、本机合成内存 API、学生/教师页面 DTO 与测试。非生产、不可部署。

## 发现与处理

在检查前端 DTO 与 Schema 覆盖时发现：Workspace 合同第 2 节要求 JSON 对象携带 `schema_version`，但此前 API 写请求、客户端 DTO 和严格 Schema 都没有这个字段。已核对活动产品决策、技术规范和质量规范，未发现另一套请求版本字段规定；本次按 Workspace 合同原文补齐，不改角色、流程或持久化边界。

所有 POST 写请求现在必须含 `schema_version: "skillshift-api/v1"`。API 在路由分派前拒绝缺失或不支持的版本；前端所有变更请求统一带版本字段。同步把合同中的“对象携带版本”明确为每个顶层请求/响应 JSON 对象携带版本，`data` 内领域 DTO 由该 API 版本下的 Schema 描述，避免将其误读为每个嵌套对象另带版本字段。严格 Schema 增加以下请求 DTO：

- `AssignmentCreateRequest`
- `EmptyRequest`（发布/开始）
- `AgentTurnRequest`
- `ProposedActionDecisionRequest`
- `SubmissionCreateRequest`
- `ReviewActionRequest`

## 文件变更

| 文件 | 变更原因 |
| --- | --- |
| `apps/agent-first/agent_first/workspace_api.py` | 统一校验写请求版本并返回显式 400 错误。 |
| `apps/workspace-client.mjs` | 表单映射和所有 POST body 携带固定版本字段。 |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json` | 严格定义请求 DTO、版本常量、枚举及文本边界。 |
| `tests/test_workspace_api.py` | 覆盖缺失/错误版本被拒绝且不创建任务。 |
| `tests/test_workspace_json_schema.py` | 校验六类请求 DTO 和额外字段/错误版本拒绝。 |
| `tests/test_workspace_wsgi.py` | 覆盖经 WSGI 适配器拒绝缺失/错误版本，并验证完整闭环仍可运行。 |
| `tests/workspace-client.test.mjs` | 校验客户端 DTO 和变更请求带正确版本。 |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | 说明当前请求与响应 wire DTO 均由严格 Schema 描述，写请求版本字段为必填。 |
| `docs/CURRENT_STATE.md` | 追加本阶段状态与 P4 未验证边界。 |

## 验证

- `python -m unittest discover -s tests -v`：**149 项，148 PASS、1 SKIP**，耗时 50.851 秒；唯一跳过仍是 Windows 符号链接创建权限，不代表符号链接安全已通过。
- `node --test tests/workspace-client.test.mjs`：**9/9 PASS**，其中新增一项直接将教师创建、教师复核、学生提交映射与 Schema required keys、常量、枚举和 allowlist 对照。
- `node --check apps/workspace-client.mjs`、教师页和学生页脚本：通过。
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`：通过。
- `python -m py_compile apps\agent-first\agent_first\workspace_api.py tests\test_workspace_api.py tests\test_workspace_json_schema.py tests\test_workspace_wsgi.py`：通过。
- 最终 `git diff --check`：通过。

## 限制与风险

- 这是本机合成 API 的请求格式变更。项目无生产 HTTP 服务或真实客户端，因此没有部署兼容性影响；真实 API 版本升级策略仍未决定。
- WSGI 循环测试仍是直接合成调用，没有启动 HTTP 服务或浏览器；页面路由、浏览器视觉、加载重试仍未验证。
- 固定 demo 角色不是认证，提交快照仍仅进程内存暂存，代码执行仍关闭，Foundation Spike 仍 PARTIAL。

## 下一步与 Git

继续在静态/直接调用范围审查 UI DTO 与 API 请求、响应 Schema 是否一致。P4 仅在合规预览路径具备后进行；不通过其他浏览器入口绕过限制。

- 分支：`codex/r0-teacher-task-authoring`。
- 本任务未提交、推送、部署或清理文件。
- Commit：`NONE`。
