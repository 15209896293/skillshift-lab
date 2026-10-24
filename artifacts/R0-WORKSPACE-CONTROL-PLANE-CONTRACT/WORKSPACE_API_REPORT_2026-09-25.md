# R0 项目工作区 API 服务层报告

- Task ID：`R0-WORKSPACE-CONTROL-PLANE-API-001`
- 当前 Gate：P3 共享控制面契约 / 本机合成服务层
- 结论：**PARTIAL**。纯内存 JSON 路由逻辑及状态契约测试可运行；没有 HTTP/WSGI 适配、前端接线、生产身份或持久化。
- Commit：`NONE`

## 产出

- `apps/agent-first/agent_first/workspace_api.py`：合成工作区服务层，支持创建/发布任务、学生开始工作、固定 Scripted Agent 提议、学生决策、合成 Artifact 引用、提交、教师复核、补正重提、事件顺序与幂等/修订校验。
- `tests/test_workspace_api.py`：16 项正/负向服务契约测试。
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`：共享对象、路由、角色、版本、事件、错误和停止边界的 Proposed 草案。
- 项目入口、应用目录和当前状态已指向该契约与下一阶段。

所有服务状态只在 Python 对象内存；关闭进程即丢失。`/demo/teacher`、`/demo/student` 是测试角色路由，不是身份认证；此模块没有 WSGI/HTTP server，不能供网页直接调用。

## 实际命令与结果

- `python -m unittest tests.test_workspace_api -v`：**失败**，因为 `tests` 目录不是 Python package（`ModuleNotFoundError`）。随后使用项目发现方式运行，不改包装结构。
- `python -m unittest discover -s tests -p test_workspace_api.py -v`：**PASS，16/16**。
- `python -m py_compile apps\\agent-first\\agent_first\\workspace_api.py`：退出码 0。
- `python -m unittest discover -s tests -v`：退出码 0；**119 tests，118 PASS，1 SKIP**。Windows 隔离探针输出临时复制 Python 路径诊断，但相关测试通过；1 个符号链接权限限制仍为 Skip，不代表 Foundation 安全问题关闭。
- `git diff --check`：退出码 0。
- 静态能力扫描 `apps/agent-first/agent_first/workspace_api.py`：未发现 HTTP 客户端、socket、子进程、Shell、动态执行或外部网络 API。
- 未启动服务、未连接浏览器、ECS、模型、密钥或文件系统执行器。

## 哈希（SHA-256）

| 文件 | 哈希 |
| --- | --- |
| `apps/agent-first/agent_first/workspace_api.py` | `C59AFF566B7672CD8DE05C1CE36E860E2E473E8684A76DB3F530DD0A11B692AC` |
| `tests/test_workspace_api.py` | `90D385F54072410FD1CDA01A4063E7D660D2E9AB979DBA42CF50D2FF865960BE` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | `C83C2FF9D79118BBDB59BA8CBF82A8B77E4F46089992526B5020D0045C0F3CB3` |

## 覆盖与限制

- 覆盖：合成任务创建、草稿对学生不可见、发布/启动修订号、幂等回放与异文冲突、角色路由拒绝、固定模型模式和禁止客户端 Provider/工具字段、学生接受建议/拒绝建议/接管状态、Artifact allowlist、提交说明长度、所有复核动作至少 8 字理由、补正重提、关闭、事件游标、16 KiB 请求限制、无执行端点。
- Artifact 目前只返回固定名称/MIME 和 `integrity_status=NOT_COMPUTED`，不伪造文件大小或哈希；接入前需要建立单一固定文件来源和哈希证据。
- 服务层由路径注入测试角色，无认证、HTTP 边界、CSRF/CORS、生产错误处理、权限租户或持久化；禁止部署或绑定非回环地址。
- 纯服务测试不证明教师/学生网页接入或浏览器状态正确。
- 教师端“认可并关闭”目前可不填理由，与该 API/旧 `EducationWorkflow.review` 要求至少 8 字理由冲突，报告在 `artifacts/R0-TEACHER-WORKSPACE/TEACHER_WORKSPACE_REPORT_2026-09-25.md` 已标 PARTIAL。
- Foundation Spike 仍 PARTIAL；本 API 不运行代码。

## 浏览器限制

本轮曾尝试将本地原型直接导航为 `file:///...`，浏览器安全策略拒绝。未尝试经其他浏览器、URL 或底层命令绕过。原先通过回环 HTTP 的两端交互 QA 证据仍在各自报告中；但任何后续前端 API 接线都必须有新的浏览器验收，在允许路径恢复之前不能宣称 UI 集成通过。

## 下一步与决策

无需产品/安全方向决策即可继续完成：补齐 API 对象完整性和响应 schema 测试；建立只绑定回环地址、只接受固定合成角色的短时 WSGI/HTTP 适配器，并做 WSGI 调用级集成测试。之后才可接教师/学生页面。

前端接线后的浏览器 QA 暂受上述浏览器策略限制。到达该阶段时需确认由用户手动打开并验收，或等应用提供合规的可浏览预览路径后再继续；无论哪种方式，都不能把纯 API 测试说成视觉/浏览器通过。

## Git 摘要

- 新增/修改：本报告、控制面契约草案、服务层、16 项测试、项目入口/状态引用。
- 工作区在本任务前已有大量未提交修改和未跟踪历史材料；均予保留，未重置/清理。
- Commit：`NONE`。
