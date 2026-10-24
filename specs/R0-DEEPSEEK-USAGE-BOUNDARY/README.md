# R0-DEEPSEEK-USAGE-BOUNDARY：DeepSeek 请求长度与用量元数据契约

## 状态

- Task ID：`R0-DEEPSEEK-USAGE-BOUNDARY-001`
- 类型：FEATURE / Gate B 本机合成费用安全契约
- 状态：**Verified / PARTIAL（2026-09-24；仅假响应和本机估算，无网络）**。
- 上游：ADR-007/008/009、`R0-DEEPSEEK-BUDGET-RECONCILIATION-RESEARCH-001`。

## 目标

1. 对 DeepSeek 固定合成请求设置 UTF-8 内容长度上限，拒绝过长输入。
2. 严格解析供应商请求 ID、返回模型标识和 Token 用量（含缓存命中/未命中）；缺失或相互矛盾的数据必须显式失败，不能伪造费用证据。
3. 给合成用量元数据提供纯函数成本估算，使用明确版本的峰/闲时价格并向上取整到分。
4. 让用量元数据留在运行时结果对象中，不写入学生提交 Manifest、普通日志或回答正文。

这项任务不连接供应商、不执行账单核对，也不把本机估算称为费用结算。

## 允许范围

- DeepSeek 请求契约、类型化用量元数据、纯函数价格估算；
- 假传输/假响应测试、合成证据 Artifact、关联规格和状态文档；
- 合成用例和费用数字，不含真实 Key、学生数据或网络。

## 禁止范围

- HTTP 客户端、真实 API 调用、账号/密钥解析、真实价格自动下载或费用扣款；
- 修改 100 元月度上限、改变模型供应商或真实发布当前模型版本；
- 把 `deepseek-flash` 标识当作永久权重版本承诺；
- 把估算金额写进学生可见提交包，或把假 usage 说成供应商账单。

## 固定合成测试快照

- 请求正文中所有消息内容总计不超过 16,384 UTF-8 字节；超出拒绝。此值是本机合成探针边界，不能直接代表课堂产品的可用长度。
- `max_tokens` 仍不超过 600。
- 定价快照 ID：`deepseek-v4.1-flash-2026-09-10-r1`。测试固定当前公开人民币表的峰/闲时费率；正式运行前必须刷新并重新版本化。
- 成本估算使用整数分/百万 Token，并向上取整；它只是本地估算。

## 验收

| ID | 条件 | 证据 |
| --- | --- | --- |
| DUB-01 | 输入内容 <=16,384 UTF-8 字节可构造请求；超限拒绝且错误不包含输入内容。 | DeepSeek contract tests。 |
| DUB-02 | 合法 usage 的请求 ID、模型和 Token 字段可解析；不一致、缺字段或非整数均拒绝。 | usage parser tests。 |
| DUB-03 | 价格快照 ID/费率显式，峰/闲时估算分开，缓存 hit/miss 分开，金额向上取整。 | calculator tests。 |
| DUB-04 | 运行时 Guidance 暴露类型化元数据，但提交 Manifest 不含供应商请求 ID、usage 或费用估算。 | runtime + vertical-slice tests。 |
| DUB-05 | 不改变“无授权时拒绝”；所有运行时测试只用 fake transport。 | runtime tests。 |
| DUB-06 | 代码编译、定向测试、证据自检及 `git diff --check` 通过。 | 文件化报告。 |

## 停止条件

需要真实输入长度、学生试用反馈、DeepSeek 账号账单/回调、密钥、费用支出、ECS、持久生产账本、告警阈值或发布时，停止本规格并交项目负责人决策。

## 实施结果

- 输入上限、严格 usage 解析、带版本价格快照与向上取整函数已实现；usage 只存在运行时 Guidance 对象，提交 Manifest 白名单不序列化该字段。
- 定向测试：契约 6、用量/估算 3、运行时 5、纵向闭环回归 8，全部通过；编译通过。
- Gate 状态仍为 PARTIAL。尚未验证供应商真实响应中的缓存字段、实际账号账单、预留额度与事后 usage 结算，未验证真实费用/告警控制。
- Artifact：`../../artifacts/R0-DEEPSEEK-USAGE-BOUNDARY/evidence.json`；报告：`../../artifacts/R0-DEEPSEEK-USAGE-BOUNDARY/USAGE_BOUNDARY_REPORT_2026-09-24.md`。
