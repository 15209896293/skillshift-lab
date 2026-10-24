# 事件分页与核心对象 Schema 验证报告

- Task ID：`R0-WORKSPACE-CONTROL-API-EVENT-SCHEMA-001`
- 当前 Gate：P3 共享 API / 本机合成契约测试
- 结论：**PARTIAL**。分页、过期游标、请求关联 ID 和核心对象必需字段在内存合成 API 中有测试；严格版本化 DTO、Artifact 内容来源和授权边界仍未关闭。
- Commit：`NONE`

## 本轮修改

- `apps/agent-first/agent_first/workspace_api.py`
  - 每次 API 调用生成一个不透明的 `req-demo-<uuid>` request ID；错误/成功 envelope 使用它，EvidenceEvent 与触发事件的 request ID 关联。
  - 相同 Idempotency-Key 重放保持业务响应数据快照，但回执使用本次 request ID；事件不重复生成。
  - Event 读取接受单一 `after_sequence`、`limit=1..50`；响应有 `next_sequence`、`has_more`。每 Workspace 合成内存最多暂留 256 条事件；旧游标明确 `409 cursor_expired`。这些固定数值只限制本机测试内存，不定义任何生产留存策略。
- `tests/test_workspace_api.py`：API 测试由 18 项增至 20 项，覆盖页长、分页、过期游标、核心对象所需字段及 request ID 与事件的关联。
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`：同步 Proposed 本机限制与未关闭的严格 schema 差距。
- `README.md`、`docs/README.md`、`docs/CURRENT_STATE.md`：同步当前状态、测试范围和证据链接。

## 实际命令与结果

- `python -m unittest discover -s tests -p test_workspace_api.py -v`：**PASS，20/20**。
- `python -m unittest discover -s tests -p test_workspace_wsgi.py -v`：**PASS，5/5**。
- `python -m unittest discover -s tests -v`：**PASS，128 项，127 PASS、1 SKIP**，运行 47.621 秒。Windows 隔离探针输出临时复制 Python 路径诊断但通过；SKIP 不构成符号链接安全证据。
- `python -m py_compile apps\agent-first\agent_first\workspace_api.py apps\agent-first\agent_first\workspace_wsgi.py tests\test_workspace_api.py tests\test_workspace_wsgi.py`：退出码 0。
- `git diff --check`：PASS；本轮源文件、规格和入口文件尾随空白扫描 0 处。
- 没有启动 HTTP/WSGI server，没有接前端/浏览器，没有访问外网、模型、密钥、真实数据、ECS 或代码执行器。

## SHA-256

| 文件 | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/workspace_api.py` | `D2ED43F5A655A1C01D4973E83830E04A9F822BCF2B1735E7767E260301197703` |
| `tests/test_workspace_api.py` | `875058FE5C67D15533BE5A04C81020023BAF55D3C45A60E06827044A1A6FA3B6` |
| `apps/agent-first/agent_first/workspace_wsgi.py` | `D2D1DE856AC05897E80A6C34DE449CCF7D6D916F7DF71EEA39AFCA490025BC94` |
| `tests/test_workspace_wsgi.py` | `E6D16E68F4359D246E885CD2325C34870B801EF9B1F313A3BE1C470E152EB306` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | `35C84AB0F5104890C848ED609FA315FAC2C2DEA918B82FAB8FEE16552F5DF34B` |

## 剩余差距和风险

- 本轮只验证核心对象的必要字段集合，不是严格 DTO：未知响应字段检查、所有枚举/状态全覆盖和兼容版本策略仍未锁定。
- Artifact 仍是固定文件名的元数据引用，`size_bytes`/`sha256` 未计算，也没有确定唯一权威文件源；不能说文件完整性已验证。
- 角色仍由 demo URL 注入，不是用户认证；租户资源授权、真实服务的并发与持久化行为均未知。
- 256 项仅是进程内测试缓存上限；重启清空，绝不可推断成生产证据保留期限。
- 浏览器安全策略限制下没有浏览器/HTTP集成检查。前端接线之前仍需要一个获准的预览/验收路径；本轮没有绕行。
- Foundation Spike 保持 PARTIAL，代码执行仍然关闭。

## 验收、下一步与 Git

- 本轮合同项（合成内存分页、游标过期、request ID 关联、核心必需字段）：**PASS**。
- 完整控制面与前后端闭环：**PARTIAL / 未开始集成**。
- 下一步：做严格 DTO 差距清单，并定义固定合成项目的唯一来源方案；对该来源能否直接采用现有学生端页面内三份文本仍需独立审查，不直接以 API 伪哈希替代证据。前端集成须等待合规浏览器复核路径。
- 当前无需产品方向决策。到达前端浏览器复核节点，若仍无可用的获准路径，需要用户提供人工验收路径。
- 当前分支 `codex/r0-teacher-task-authoring`。跟踪文件 diff stat 不含大量此前未跟踪文件且混有既有工作区改动；本轮新增文件及旧改动均保留。
- Commit：`NONE`。
