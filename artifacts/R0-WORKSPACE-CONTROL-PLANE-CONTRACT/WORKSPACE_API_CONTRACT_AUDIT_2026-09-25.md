# 工作区 API 契约审计补充

- Task ID：`R0-WORKSPACE-CONTROL-API-CONTRACT-AUDIT-001`
- 当前 Gate：P3 共享 API / 本机合成契约
- 结论：**PARTIAL**（两处确定性边界缺陷已修正；对象/schema、Artifact 来源、授权及分页缺口仍开放）
- Commit：`NONE`

## 发现与修正

1. ReviewAction 的错误文本承诺“至少 8 个非空白字符”，实现原来按字符串总长度计数，内部空格可以凑足门槛。现在按 Unicode `isspace()` 排除空白后计数；新增负向测试。
2. 幂等缓存原来存放并返回同一个可变 ApiResponse。Agent 回合建立的 ProposedAction 在后续学生决策时会原地更新，旧幂等回执因此变化。缓存写入、首次返回和重放现在均做深拷贝；新增回归测试证明决策后重复 Agent 请求仍返回原始 `PROPOSED` 回执。既有闭环测试调整为检查服务当前状态，不再依赖调用方响应对象被后续操作修改。

## 修改文件

- `apps/agent-first/agent_first/workspace_api.py`：修正理由长度规则与幂等响应快照。
- `tests/test_workspace_api.py`：从 16 项增至 18 项，新增上述两个案例并更新状态断言。
- `docs/CURRENT_STATE.md`、`docs/README.md`、`README.md`：更新测试计数、工作区 API/WSGI 阶段和报告引用。

## 实际命令与结果

- `python -m unittest discover -s tests -p test_workspace_api.py -v`：**PASS，18/18**。
- `python -m unittest discover -s tests -p test_workspace_wsgi.py -v`：**PASS，5/5**。
- `python -m py_compile apps\agent-first\agent_first\workspace_api.py apps\agent-first\agent_first\workspace_wsgi.py tests\test_workspace_api.py tests\test_workspace_wsgi.py`：退出码 0。
- `python -m unittest discover -s tests -v`：**PASS，126 项，125 PASS、1 SKIP**，运行 47.330 秒；Windows 隔离测试有临时复制 Python 路径诊断输出但通过。SKIP 不构成安全证明。
- `git diff --check`：PASS；所列源文件与规格/状态文件尾随空白扫描 0 处。
- 审计过程中有一次预期断言失败：WSGI 413 状态短语在 Python 平台间措辞不同，断言已改为校验码前缀，随后 WSGI 5/5 及全量 126 项回归通过。API 新修正后的全量回归也已重新运行。

## SHA-256

| 文件 | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/workspace_api.py` | `3D2E5A3667093CDC36C624EAFA5E93706D068CC22AE2049B9652B256983B51A3` |
| `tests/test_workspace_api.py` | `A97FF6A96B691D538A1782B397E6D883B61B69C9DB3334B810E2557582D4B967` |
| `apps/agent-first/agent_first/workspace_wsgi.py` | `D2D1DE856AC05897E80A6C34DE449CCF7D6D916F7DF71EEA39AFCA490025BC94` |
| `tests/test_workspace_wsgi.py` | `E6D16E68F4359D246E885CD2325C34870B801EF9B1F313A3BE1C470E152EB306` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | `BEDABDCD2ED5561DF4A27B0F417D943489AB22BBB8C9A5819906B317D7054A3E` |

## 尚未通过的契约项 / 风险

- Artifact 当前没有固定项目文件的单一权威来源，也没有可核验内容哈希；不得伪称文件完整性已验证。
- 事件分页未实现有界页长与 cursor expiry；request_id 仍是演示常量，不能用作生产关联 ID。
- 对象 schema、长期授权、身份/租户边界、持久化和错误语义仍不完整；整个契约保持 Proposed。
- WSGI 适配器只做直接调用级边界测试，不能限制 server/proxy 的网络拓扑，不得启动供真实用户访问或部署。
- 未打开网页或连接前后端。之前的本地文件导航曾被浏览器安全策略拒绝，本轮未用其他方式绕过；后续真实浏览器集成需要获准的产品预览路径。
- Foundation Spike 代码执行安全路线未变，仍 PARTIAL。

## 下一步

继续在合成范围建立 Artifact 固定来源/内容摘要与事件分页契约测试，并做 DTO/schema 差距表；完成后再评估是否满足接前端条件。前端纵向接线保持未开始，直至能够完成合规浏览器复核。

## Git

- 分支：`codex/r0-teacher-task-authoring`。
- 跟踪文件 diff stat：9 个既有被修改文件，116 行新增、119 行删除；该统计不含大量此前已存在的未跟踪文件，也不代表它们全由本任务创建。新增文件清单以 `git status --short` 为准。
- 所有既有未提交状态均保留；没有 reset、clean、删除、提交、推送或部署。
- Commit：`NONE`。
