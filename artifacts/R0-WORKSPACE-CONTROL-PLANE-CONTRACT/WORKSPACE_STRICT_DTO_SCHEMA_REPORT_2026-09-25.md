# 本机合成 API 严格 DTO Schema 报告

- Task ID：`R0-WORKSPACE-CONTROL-STRICT-DTO-SCHEMA-001`
- 当前 Gate：P3 共享 API 合同；本机合成 wire DTO 形状验证
- 结论：**PARTIAL**（当前合成响应有严格 Schema 校验；生产 DTO、Artifact 内容、真实身份/授权和 HTTP 集成均未关闭）
- Commit：`NONE`

## 文件变更及原因

- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json`：定义当前实际线缆格式的严格 JSON Schema，使用 `additionalProperties: false`。覆盖成功/错误 envelope、Task、Assignment、Workspace、ArtifactReference、EvidenceEvent、EventPage、AgentTurn、ProposedAction、Submission、ReviewAction、Remediation；评语限制 8 个非空白字符，文本还用 `x-maxUtf8Bytes` 标注字节上限。
- `tests/test_workspace_json_schema.py`：使用标准 JSON Schema Draft 2020-12 validator 检查 Schema 本身和真实合成 API 流程产生的各个对象，并验证未知字段、错误枚举、空白评语和超长事件页被拒。
- `requirements-test.txt`：将 `jsonschema==4.26.0` 声明为测试工具依赖；不是产品运行时依赖。本机此前已安装同版本，本轮没有安装包或联网。
- `tests/test_workspace_api.py`：新增精确 128 UTF-8 字节标题接受、超限拒绝案例。
- `specs/.../README.md`、`docs/quality/QUALITY_SPEC.md`、`apps/README.md`、`docs/README.md`、`docs/CURRENT_STATE.md`、`README.md`：说明 strict schema 只绑定当前合成 wire 形状、测试依赖、UTF-8 字节限制与阶段结果。

## 实际执行命令与结果

- `python -c "import importlib.util; print('jsonschema=' + str(importlib.util.find_spec('jsonschema') is not None))"`：PASS，模块已存在。
- `python -c "import jsonschema; print(jsonschema.__version__)"`：版本 `4.26.0`（Python 输出弃用提示仅针对读取包内 `__version__` 属性，不影响测试）。
- `python -m unittest discover -s tests -p test_workspace_json_schema.py -v`：**PASS，4/4**。
- `python -m unittest discover -s tests -p test_workspace_api.py -v`：**PASS，21/21**。
- `python -m unittest discover -s tests -p test_workspace_wsgi.py -v`：**PASS，5/5**。
- `python -m unittest discover -s tests -v`：**PASS，133 项，132 PASS、1 SKIP**，运行 46.400 秒。Windows 隔离探针有临时复制 Python 路径诊断但通过；1 项 SKIP 不构成安全证据。
- `python -m py_compile apps\agent-first\agent_first\workspace_api.py tests\test_workspace_api.py tests\test_workspace_json_schema.py`：退出码 0。
- `git diff --check`：PASS；本轮有关文件尾随空白扫描为 0 处。
- 没有启动 HTTP server，没有接入前端，没有浏览器操作、外网访问、真实模型/Key/数据、ECS、代码执行、部署或 Git 写操作。

## SHA-256

| 文件 | SHA-256 |
| --- | --- |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json` | `CF99B2004E0FC6DF6376D6D15837490EE6468FBBDD4060479B203AAC5EC1CBC5` |
| `tests/test_workspace_json_schema.py` | `4F727011DA3CAB0B32AEB4B4ADFBA7031705D72631928AC4A328A49D387EF5F1` |
| `requirements-test.txt` | `756CC9E506AE4EE1A6F6C0507088B5CFC0DC8BA350FB2D2D46F1FFA72033ADB6` |
| `tests/test_workspace_api.py` | `5EA8B1257FDA64F8D587F14AD661D0D50BD258B6968C770284EC08F30159A75C` |
| `apps/agent-first/agent_first/workspace_api.py` | `D2ED43F5A655A1C01D4973E83830E04A9F822BCF2B1735E7767E260301197703` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | `2AA74A4675CF3F805D82D6727C025788FBFA73F8ABF60F579DD0AD2419398050` |

## 通过范围与剩余风险

- PASS：当前固定合成请求走出的核心成功/错误 DTO 符合 strict Schema；未知字段和非法枚举不能通过 schema 测试；API 实现另以 UTF-8 字节检查任务文本。
- PARTIAL：Schema 是本机合成线缆格式，不是已接受的生产 DTO。JSON Schema `maxLength` 以字符计数，不能取代 API 的 UTF-8 字节验证；状态/端点矩阵并未全部穷尽。
- Artifact DTO 有意只允许 `integrity_status=NOT_COMPUTED`，不产生 size/hash，也没有选定唯一权威文件来源。服务端无法证明学生页面编辑过的内容等于引用的固定文件。
- 不提供用户认证、租户/资源级授权或持久化；`/demo/...` 身份注入不可部署。
- WSGI 仅直接调用级测试；前后端未接线，也未获浏览器集成验收。
- Foundation Spike 仍 PARTIAL；代码执行继续关闭。

## 下一步、决策与 Git

- 接口基础可继续完成静态合同工作，不需要当前产品决策。
- 下一步审查固定合成项目三份文件的唯一来源：当前学生页面把内容内嵌于 JavaScript，服务端只有文件名 allowlist，教师演示又有占位数据；先给出一份来源/差异清单，再决定能否以纯合成只读 fixture 建立内容摘要，不能直接伪造哈希。
- 前端接口接线前还需有获准的浏览器验收路径。到达该阶段时，我先继续其他可验证工作，不会擅自绕过安全策略。
- 当前分支 `codex/r0-teacher-task-authoring`。工作区含此前大量未提交/未跟踪内容，全部保留；`git diff --stat` 不包含未跟踪文件且混有先前改动。
- Commit：`NONE`。
