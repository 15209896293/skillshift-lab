# R0 学生项目工作区原型报告

- Task ID：`R0-STUDENT-WORKSPACE-001`
- 当前 Gate：产品 UI 原型阶段（B 方案 P2）
- 结论：**PASS（仅本机合成交互原型范围）**；不代表真实 Agent、真实用户或安全代码执行已就绪。
- Commit：`NONE`

## 本次交付

独立学生工作区页面包含任务要求、固定合成 Python/CSV/README 文件、可编辑代码区、任务内 Agent 演示回复、固定修改差异、学生接受/拒绝/接管、验证说明提交表单。多个文件间的未保存编辑保留在当前页面内存，刷新清空。运行控件始终禁用并说明代码执行 Gate 未开放。

## 验收

| 条件 | 结果 | 证据 |
| --- | --- | --- |
| SW-01 独立入口且合成边界显著 | PASS | `apps/student-web/index.html` 独立页面；页头/任务区标为“合成学生工作区”与演示模式。 |
| SW-02 浏览并编辑项目文件 | PASS | 浏览器切换 main.py / orders.csv；编辑后切出再切回，页面内修改仍在。 |
| SW-03 Agent 建议显式模拟且学生决定 | PASS | 固定回复可打开差异；验证了拒绝、接受（只更新页面编辑区）和接管编辑；接受时改动明确未运行/未落盘。若内容不匹配，接受会拒绝覆盖。 |
| SW-04 没有执行能力 | PASS | “运行”按钮 DOM 状态为 disabled；代码与 Agent 边界写明无执行/联网/真实模型。静态扫描未发现网络、浏览器存储、动态 eval 或子进程 API。 |
| SW-05 提交要求任务相关验证说明 | PASS | 空说明时浏览器原生必填校验拦截；填写异常、验证与不确定性后记录本机演示状态。 |
| SW-06 刷新及服务边界明确 | PASS | 页面明示编辑不自动保存、刷新清空；提交结果不发送给教师或后台；Agent 回复固定演示内容。 |
| SW-07 语法、回归和浏览器 QA | PASS（当前范围） | 前端语法检查通过；项目全量 103 项测试通过、1 项跳过；浏览器交互可复核。 |

## 执行记录

- `node --check apps\\student-web\\app.js`：退出码 0。
- `node --check apps\\teacher-web\\app.js`：退出码 0。
- `python -m unittest discover -s tests -v`：退出码 0；103 tests，`OK (skipped=1)`。Windows 隔离探针有临时副本 Python 路径提示，但相应测试通过；这不是安全隔离完成证据。
- 静态边界扫描：新教师/学生前端未发现 `fetch`、`XMLHttpRequest`、`WebSocket`、浏览器存储、`eval`、外部窗口导航或子进程接口。
- 两个静态原型分别通过 `http://127.0.0.1:8767/` 和 `http://127.0.0.1:8768/` 返回 HTTP 200。服务只绑定回环地址，验证后停止；页面没有连接 API。
- `git diff --check`：退出码 0。
- 浏览器交互：文件切换/编辑保留；Agent 固定回复/差异查看；接受、拒绝、接管；空提交拒绝和验证说明提交；运行按钮禁用。页面截图已视觉检查，但未保存独立截图 Artifact。

## Artifact 哈希

SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `apps/student-web/index.html` | `81FE917B5E28825F319490155935B846699D51FCC61939FA0AACD9579B7CF52B` |
| `apps/student-web/styles.css` | `52E85DF6626DE3DB6DC597BC2AC36E3A5B7E3FC133328C2C969E5ED1625CA2FB` |
| `apps/student-web/app.js` | `DBEE7AA781FF25D467A9ACA43E05742E3E6D101489BD5F4D28C5795EDD347EC8` |

## 限制与风险

- Agent 全部是固定示例，没有模型理解能力；提交、文件与复核不会跨刷新或到达教师端。
- 文件只在页面内编辑，未连接本机文件系统；编辑器尚无真正代码编辑器的语法高亮、版本控制或协作能力。
- 运行、Shell、依赖安装、网络工具、真实身份、真实材料、持久后端、生产模型与部署均未实现/未获此原型授权。
- 尚无学生使用/教师走查；本界面不证明易用性、课程适配、学习效果或研究结论。

## 下一步

学生前端原型可作为 P2 的本机合成验证结果。下一项为 **R0-WORKSPACE-CONTROL-PLANE-CONTRACT-001**：冻结教师与学生共享的 Assignment/Task、Workspace Session、Agent Turn/Proposed Action、Artifact Reference、Evidence Event、Submission、Review Action、Remediation 的最小字段与状态；明确角色授权、版本/幂等、刷新同步、错误与审计边界。契约通过文档审阅和本机合成契约测试后，再接无真实数据/模型/部署的后台纵向切片。

无需用户决策即可继续合成 API 契约与本机模拟服务。若接入真实 DeepSeek、密钥/计费服务、真实用户数据、ECS/部署或任何学生代码执行，则必须停在对应 Gate 并提出决策。

## Git 摘要

- 新增：`specs/R0-STUDENT-WORKSPACE/README.md`、`apps/student-web/{index.html,styles.css,app.js}`、本报告。
- 更新：`apps/README.md`、`README.md`、`docs/README.md`、`docs/CURRENT_STATE.md`，同步两端原型与当前下一阶段。
- 工作区已有大量无关修改与未跟踪资料；本任务没有清理、复位或提交这些文件。
- Commit：`NONE`。
