# 固定合成项目 Artifact 来源审计

- Task ID：`R0-WORKSPACE-ARTIFACT-SOURCE-AUDIT-001`
- 当前 Gate：P3 固定合成项目材料来源审计
- 结论：**PARTIAL / 源文件完整性不能验证**
- Commit：`NONE`

## 审计范围与证据

只检查仓库中固定演示项目 `orders-audit-v1` 的代码/数据/文档来源，不运行项目、不接前端、不启动 HTTP 服务。

| 位置 | 已观察到的内容 | 能证明什么 / 不能证明什么 |
| --- | --- | --- |
| `apps/student-web/app.js` | `main.py`、`orders.csv`、`README.md` 作为 JS 字符串内嵌在页面代码中；CSV 有 O-104/O-105/O-106 三行。 | 证明当前学生页面有固定静态文本；不是独立项目文件，也不是服务端/Workspace Artifact。页面编辑变更仅在内存。 |
| `apps/teacher-web/index.html` | 静态表格重复显示同三笔订单；“orders_checked.csv”在时间线文案中明确是合成占位、待实际工作区接入。 | 是教师端展示样例，不是学生实际输出文件或由程序运行产生的文件。 |
| `apps/agent-first/agent_first/workspace_api.py` | `orders-audit-v1` ID、三个文件名和 MIME allowlist；ArtifactRef 标为 `FIXED_SYNTHETIC` 与 `NOT_COMPUTED`。提交只接收文件名和说明，不接收学生编辑后的内容。 | 能拒绝任意路径/文件名；不能证明内容、大小、哈希，也不能表示提交时学生缓冲区的版本。 |
| `apps/student-web/app.js`（Agent 面板代码） | 页面固定脚本回复引用 O-105 的 2 × 89 与 160 的差异。 | 是静态/脚本化建议，不读取实际项目文件或运行代码；不能当作执行/验证证据。 |

只读搜索命令 `rg -n --hidden -g '!**/.git/**' -g '!**/__pycache__/**' -g '!**/node_modules/**' "order_id,quantity,unit_price,amount|O-105|find_inconsistent_orders|orders-audit-v1|artifact-main-py-v1" apps specs docs artifacts` 显示实际内容主要位于上述学生 JS 与教师静态 HTML；没有发现独立的同名 canonical fixture 文件。`rg --files apps` 显示 Apps 中也没有该项目材料的独立文件集。

## 实际文件 SHA-256

| 文件 | SHA-256 |
| --- | --- |
| `apps/student-web/app.js` | `DBEE7AA781FF25D467A9ACA43E05742E3E6D101489BD5F4D28C5795EDD347EC8` |
| `apps/teacher-web/index.html` | `08BE5964974792FD2FD636B1173B7F440EFC018EFACFF9C0FB08D5EDCCB01016` |
| `apps/agent-first/agent_first/workspace_api.py` | `D2ED43F5A655A1C01D4973E83830E04A9F822BCF2B1735E7767E260301197703` |

## 产品/架构判断

- 当前 `FIXED_SYNTHETIC` 只表示固定文件名 allowlist，并不表示文件内容已固定、可复现或已计算完整性；这个命名的语义边界需要保持明确。
- 学生端 UI 的“提交”目前只是浏览器内演示。API 提交的 Artifact 名称不能反映页面编辑后的代码内容；不能让教师误以为读到了真实文件。
- 建议作为 **Proposed** 进入下一小步：在 `fixtures/orders-audit-v1/` 建立与页面相同的纯合成 `main.py`、`orders.csv`、`README.md`，加机器可读 manifest 记录版本、MIME、逐字节大小和计算得到的 SHA-256；测试验证 manifest 与原始字节一致。
- 这一步只能建立“起始 fixture”权威源。浏览器页面继续内嵌数据时仍存在重复；在获准的 UI QA 路径恢复前，不改前端加载方式，不宣称已消除重复。
- fixture 哈希仅证明仓库内起始示例字节；不能证明学生编辑版本，也不等同提交的不可抵赖性。后续若传送编辑缓冲区，仍须定义临时保存/删除和响应体日志边界；生产持久化与真实用户数据仍需独立门禁。
- 教师端的 O-105 静态表仍只是示例，不产生 `orders_checked.csv`。无代码运行，不给“已验证结果”标识。

## 机器证据与 Git

- 只读审计；本审计任务仅新增本报告。没有修改 Student/Teacher UI、API、项目文件或规格之外的权威决策。
- 命令结果：搜索完成，找到两个不同展示载体和一个文件名 allowlist；没有找到 canonical 文件目录。
- `git diff --check`：通过（跟踪文件差异）；本报告新增文件的尾随空白扫描为 0。
- 当前分支：`codex/r0-teacher-task-authoring`。跟踪文件 diff stat 受此前既有工作区改动影响且不包含未跟踪文件；未清理或覆盖任何内容。
- Commit：`NONE`。
