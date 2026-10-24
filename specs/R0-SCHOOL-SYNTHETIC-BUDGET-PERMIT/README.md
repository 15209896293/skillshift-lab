# R0-SCHOOL-SYNTHETIC-BUDGET-PERMIT：学校预算许可契约

## 状态

- Task ID：`R0-SCHOOL-SYNTHETIC-BUDGET-PERMIT-001`
- 类型：FEATURE / Gate B 本地预算许可
- 状态：**Implemented / Verified（内存、合成、无真实费用）**。
- 上游：ADR-008、ADR-009。

## 目标

验证未来学校管理员启用合成 DeepSeek 探针时，运行时能够在请求前保守预留预算，默认拒绝，并在 100 元月度硬上限后停止许可。

## 禁止范围

- 真实收费、真实 Key、供应商账单、数据库、管理员 Web、身份/租户、跨进程/跨服务器账本、部署或网络请求；
- 教师/学生自行提高预算、切换 provider/model、真实数据、工具、联网搜索或自动评分。

## 验收

| ID | 条件 | 最小证据 |
| --- | --- | --- |
| SBP-01 | 默认策略拒绝，不预留金额。 | unit test。 |
| SBP-02 | 启用后每次先预留，达到 10,000 分后拒绝。 | unit test。 |
| SBP-03 | provider、访问模式、数据分类或模型不匹配时拒绝。 | negative test。 |
| SBP-04 | 并发 30 次请求不能突破 10,000 分上限。 | concurrency test。 |
| SBP-05 | 不能通过策略把上限提高到 100 元以上。 | negative test。 |

## 停止条件

需要真实计费、真实 Key、跨服务账本、身份/租户、管理员 UI、部署或真实调用时，停止在本规格范围内推进；先替换为持久预算服务并完成独立合成探针授权。

