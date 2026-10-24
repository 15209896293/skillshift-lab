# apps

应用代码目录。

截至 2026-10-09，除下述合成 Harness/原型外，`studio-web/` 已有独立 React + TypeScript + Vite 工程，包含教师/学生路由和本机合成 API 调用代码。该工程截至交接只做源码只读检查，尚无本轮 build、lint、服务启动或浏览器验收证据。全项目状态见 `../docs/PROJECT_STATUS_2026-10-09.md`。

`studio-web/` 是当前 Web 前端实现资产，不决定桌面/Web 的长期产品形态，也不证明登录、真实模型、生产 API、持久化或真实用户能力。详细页面、启动条件与限制见 `../docs/HANDOFF_STUDIO_WEB_FRONTEND_CONTINUATION_2026-10-09.md`。

`agent-first/` 是经 `specs/R0-LOCAL-WEB-PROTOTYPE/README.md` 约束的本机合成教学流程原型，复用 Gate A 的确定性工作流；包含教师/学生演示页面和仅绑定回环地址的临时 API，不包含登录、持久数据、真实模型、密钥、学生代码执行或部署能力。

其中 `agent_first/workspace_api.py` 是新的项目工作区 API 逻辑测试适配器；`agent_first/workspace_wsgi.py` 提供直接调用级、回环来源校验的合成 WSGI 边界；Task121 已用临时 `127.0.0.1` HTTP socket 验证 P3 合成闭环，服务已关闭。Task122、125、126、127、128 已通过 Microsoft Edge/Playwright 对临时 loopback HTTP 页面进行有限 UI 验收，覆盖多轮教师补正闭环、学生提交回执丢失后的刷新不确定状态与局部读取失败恢复、教师发布回执丢失后的同请求重试，以及整页刷新后的任务目录读回（没有再次发布）。它们不是生产服务或浏览器全量验收；Task128也未验证服务进程重启或持久化。`teacher-web/` 与 `student-web/` 的 DTO 调用仍由 mock-fetch、静态 DOM 和直接 WSGI 测试覆盖。API 的提交快照能力仅接收三个固定逻辑文件的有界合成文本，在内存中计算 SHA-256 并供教师复核队列读取，不访问主机路径、不执行、不落盘。`specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json` 描述当前合成线缆 DTO 的严格形状，由 `requirements-test.txt` 中的 JSON Schema 测试工具校验。URL 中的教师/学生 demo 角色不是认证，任何相关代码都不能部署。

`teacher-web/` 是独立教师工作台的静态合成原型，规格见 `specs/R0-TEACHER-WORKSPACE/README.md`；代码会映射创建/发布 DTO、读取合成复核队列和快照并提交教师动作。没有账户、真实学生或运行中的后端服务。

`student-web/` 是独立学生项目编码工作区的静态合成原型，规格见 `specs/R0-STUDENT-WORKSPACE/README.md`；代码会读取已发布的合成任务、调用 scripted-demo、记录学生决定并发送 allowlist 文本快照，读取教师补正理由。文件草稿仍只在页面内存，API 任务与提交只在服务进程内存，运行按钮保持关闭。

`student-studio/` 和 `execution/` 中的本机代码执行实验仍是独立的 Foundation Spike，不因上述网页原型而获得可用结论。

`../fixtures/orders-audit-v1/` 是候选合成项目来源，含固定 Python/CSV/说明文件与 SHA-256 manifest。学生页面仍保留经一致性测试的内嵌副本，fixture 尚未成为 API/教师/学生共同的唯一权威来源，也不启用代码执行。
