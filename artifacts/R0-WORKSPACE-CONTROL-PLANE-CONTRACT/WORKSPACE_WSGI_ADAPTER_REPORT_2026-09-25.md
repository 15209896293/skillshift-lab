# 本机合成工作区 WSGI 适配器报告

- Task ID：`R0-WORKSPACE-CONTROL-WSGI-001`
- 当前 Gate：P3 共享工作区 API 契约 / 本机合成适配层
- 结论：**PARTIAL**（直接 WSGI 调用边界通过；未启动 HTTP 服务、未连接前端）
- Commit：`NONE`

## 目标与边界

为已存在的纯内存 `WorkspaceApi` 增加一个可由 WSGI 调用的回环合成适配器，并以假 WSGI 环境测试，不启动监听端口。适配器拒绝非回环 `REMOTE_ADDR`、限制方法为 GET/POST、限制请求体为 16 KiB、POST 必须为 JSON、转发幂等与 If-Match 头、响应禁止缓存；内部异常只返回通用错误，不反射异常内容。

它仍使用 `/demo/teacher` 和 `/demo/student` 固定演示路由，不是身份认证。代码无法约束部署服务器或代理拓扑，不能以 `REMOTE_ADDR` 检查代替网络绑定与正式认证。本适配器只可用于本机合成验收，不得部署或对非本机用户开放。

## 修改文件

- `apps/agent-first/agent_first/workspace_wsgi.py`：增加仅用于本机合成测试的 WSGI 边界。
- `tests/test_workspace_wsgi.py`：增加 5 项边界与错误响应测试。
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`：更新适配器现状和接前端前置限制。
- `README.md`、`docs/README.md`、`docs/CURRENT_STATE.md`：同步产品入口、当前 Gate 和限制。

## 实际验证

- `python -m unittest discover -s tests -p test_workspace_api.py -v`：**PASS，16/16**。
- `python -m unittest discover -s tests -p test_workspace_wsgi.py -v`：**PASS，5/5**。最终实现的一次全套回归之后又单独重跑，结果通过。
- `python -m py_compile apps\agent-first\agent_first\workspace_wsgi.py tests\test_workspace_wsgi.py`：退出码 0。
- `python -m unittest discover -s tests -v`：**PASS，124 项；123 PASS，1 SKIP**，运行约 47 秒。Windows 隔离探针打印若干临时复制 Python 路径诊断，但全套命令退出码 0；SKIP 不作为安全路线通过证据。
- `git diff --check`：PASS；新增文件尾随空白扫描：0 处。
- 没有启动 HTTP 服务，没有打开浏览器，没有联网、模型调用、Key、真实数据、ECS、代码执行或部署。

## 哈希（SHA-256）

| 文件 | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/workspace_wsgi.py` | `D2D1DE856AC05897E80A6C34DE449CCF7D6D916F7DF71EEA39AFCA490025BC94` |
| `tests/test_workspace_wsgi.py` | `E6D16E68F4359D246E885CD2325C34870B801EF9B1F313A3BE1C470E152EB306` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | `BEDABDCD2ED5561DF4A27B0F417D943489AB22BBB8C9A5819906B317D7054A3E` |

## 已知限制与风险

- 没有由真实 WSGI HTTP server 发出的网络集成证据，也没有浏览器接入证据；测试直接构造 WSGI environ。
- demo URL 注入固定角色，不安全用于真实用户；不能用反向代理对外暴露。
- API 状态进程内易失；刷新页面并不会调用此适配器，也不能从此报告推断跨端状态同步。
- Artifact 仅为固定引用，内容哈希仍为 `NOT_COMPUTED`；身份授权、事件分页/过期游标、对象 schema 仍需补齐。
- 前端浏览器路径此前遭安全策略拒绝；未改用其他 URL/浏览器表面绕过。后续 UI 接线需待允许的产品预览路径，再由人工复核视觉和浏览器状态。
- Foundation Spike 的隔离失败/部分项没有变化；本任务没有代码执行能力。

## 验收与后续

- WSGI边界：**PASS**（仅在直接调用、合成环境下）。
- 控制面契约：**PARTIAL**。
- 前后端纵向闭环：**未开始**。
- 下一步可安全自动推进：补齐 DTO/schema、事件页与 Artifact 权威内容/哈希契约测试，检查并修正教师认可理由与服务域规则差异；前端接线之前需要能获得合规浏览器复核路径。不得将当前适配器启动或部署。
- 是否需要本轮产品决策：**否**。只有进入前端实网接线且无合规预览路径时，才需用户提供手动验收或产品内预览通道。

## Git 摘要

- 当前分支：`codex/r0-teacher-task-authoring`。
- 本任务文件包括 1 个新适配器、1 个新测试、1 个报告和规格/入口文档中对应状态更新。
- 工作区此前已有大量未提交/未跟踪内容；全部保留。`git diff --stat` 只统计跟踪文件，未覆盖新增文件；未运行清理或覆盖操作。
- Commit：`NONE`。
