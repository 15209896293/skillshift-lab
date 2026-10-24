# DeepSeek 预算与实际费用对账研究（PCP-17）

- Task ID：`R0-DEEPSEEK-BUDGET-RECONCILIATION-RESEARCH-001`
- Gate：Gate B；整体 PARTIAL
- 结论：**PASS（官方公开资料与本地契约静态审阅）；PCP-17 仍未关闭**
- 状态：Proposed research
- 查询日期：2026-09-24

## 1. 结论

项目已确认 100 元/月硬上限，但当前实现只能在发请求前做本地额度许可，不能计算真实账单或把供应商账单与请求关联。真实调用前至少要补上：有限制的输入长度、价格版本快照、响应 Token 与模型版本记录、未知结果保留预留、供应商账户级对账来源和人工告警责任。

当前 DeepSeek 官方模型名 `deepseek-flash` 对应 V4.1-Flash；价格按命中缓存、未命中缓存、输出 Token 和北京时间峰/闲时分别计费。官方价格说明同时提示价格可能变化。每次正式合成探针都应记录调用当日价格快照和响应模型信息。此前 ADR-007 也明确 `deepseek-flash` 是模型档案标识，不保证永久对应同一权重版本。

## 2. 官方计费事实（2026-09-24 查询）

| 项目 | 高峰价 | 闲时价 | 来源 |
| --- | ---: | ---: | --- |
| `deepseek-flash` 输入缓存命中 / 百万 Token | ¥0.04 | ¥0.02 | 官方中文价格表 |
| 输入缓存未命中 / 百万 Token | ¥2.00 | ¥1.00 | 官方中文价格表 |
| 输出 / 百万 Token | ¥8.00 | ¥4.00 | 官方中文价格表 |

高峰时段为北京时间周一至周五 9:00–12:00、14:00–18:00，其余为闲时。计费按实际输入/输出 Token 量；缓存命中和未命中分开统计。对应费用从充值余额或赠送余额扣除，赠送余额优先。官方页面说明价格可调整。[DeepSeek 模型与价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)

官方文档称 `deepseek-flash` 当前服务 V4.1-Flash；旧 V4 Flash 版本已下线。[V4.1-Flash 发布说明](https://api-docs.deepseek.com/zh-cn/news/news260910/)

官方 API 响应包括 Token 用量字段；Chat Completions 还可报告缓存命中/未命中数量。官方文档建议以响应实际 Token 用量而非字符换算估算。[Token 用量说明](https://api-docs.deepseek.com/zh-cn/quick_start/token_usage/)、[Chat Completions API](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion/)

这些公开资料没有证明当前存在本项目可用的账单导出 API、项目级分账 API 或扣费回调。正式账单/余额变动记录的可用形式仍需在未来授权的供应商账号内只读核验。

## 3. 现有代码证据与缺口

只读审阅路径：`apps/agent-first/agent_first/deepseek_contract.py`、`deepseek_runtime.py`、`school_budget.py` 和 `synthetic_budget_ledger.py`。

1. `DeepSeekChatContractAdapter` 固定 `max_tokens <= 600`，但没有固定 `task_goal` 或 `student_question` 的最大长度。输出有上限，输入 Token 费用仍没有由代码保证的上限。
2. `SchoolMonthlySyntheticBudgetPermit` 预留金额默认 100 分（¥1），使用进程内计数；不能跨进程、重启或真实账单核对。SQLite 合成生命周期契约不能自动替代生产预算服务。
3. `DeepSeekSyntheticRuntimeAdapter` 从响应中只提取回答正文，忽略 `usage`、供应商返回的 `model` 和请求 ID；预算协议只有 `authorize`，没有 settle/reconcile API。
4. 响应正文不应为了对账而写入账本或日志。只需保留有界的费用/模型元数据和随机关联 ID。
5. 预留 100 分只有在请求输入大小有硬上限并按峰时单价验证最坏费用后，才能证明大于单次最大估算额；当前输入无界，不能据此保证一次调用不会超过预留额。

## 4. 建议的 Proposed 账单流程

```text
建立价格快照和输入/输出上限
  → 计算峰时最坏金额并事务预留
  → 发出冻结的合成请求
  → 成功：保存响应模型/Token 元数据，按实际用量计算估算额
  → 超时或断连：保持待对账，占用原预留
  → 以供应商账户扣费明细核对估算额，确认后结算
  → 到达 100 元硬上限或账单来源异常：停止新请求并告警
```

- 费用预估按峰时费率计算，不将缓存折扣提前抵扣可用预算。
- 价格改变或响应模型出现未审核版本时，暂停请求，重新冻结价格/模型记录并跑合成回归。
- 实际账单是财务对账依据，API usage 是逐请求交叉核对依据；两者不一致要进入人工处理，不自动覆盖或释放账本。
- 建议候选告警：预算使用 70% 提醒、90% 紧急提醒、100% 服务端拒绝；阈值仅 Proposed，须项目负责人和费用责任人确认。
- 如果供应商没有账户级按项目用量导出，则先使用独立的项目 API 凭据/账户并保留人工月结记录；若账户还被其他系统使用且无法拆分，不能证明 SkillShift 遵守 100 元上限。

## 5. 后续实现规格建议

下一项本机工作可以在完全无网络的合成测试中：

1. 给 DeepSeek 请求设置固定 UTF-8 字节输入上限，并以 peak price + 600 输出 Token 计算保守预留上界；若输入超过上限则拒绝。
2. 定义 `usage` schema、模型 ID、价格版本、关联 ID及金额分计算规则；不保存内容文本。
3. 扩展假传输/假账本测试以覆盖成功、缺失 usage、 malformed usage、超预算响应、未知结果和模型 ID 漂移。
4. 生产账本运行时仍保持默认关闭；没有真实账单来源与用户对真实账号的批准前，不调用供应商。

实际输入字节上限应通过合成负向测试和定价最坏情况计算后确定。不能只依赖提示词约定或字符到 Token 的平均比率。

## 6. 需要后续项目负责人决策的事项

- 100 元上限适用于 SkillShift 专用 DeepSeek 账户，还是学校多人共用账户？若共用，必须确认分账证据。
- 候选告警阈值采用 70% / 90% / 100% 是否可接受？（100% 硬拒绝已由现有决策确定，前两项只是提醒。）
- 未来费用责任人、月度账单复核人和对账周期是谁？

以上决策不阻塞本地合成技术契约；但没有账户范围、正式账单来源和责任人，PCP-17 不得关闭，也不得真实调用。

## 7. 官方账单接口范围与后续实现状态更正（2026-09-24）

Task ID：`R0-DEEPSEEK-BILLING-SOURCE-RECHECK-001`。复核官方文档后确认：已公开记录的 `GET /user/balance` 只返回当前余额可用状态及按 CNY/USD 拆分的总余额、赠余额、充值余额；该接口 schema 没有逐笔调用、月度支出或发票字段。[官方查询余额 API](https://api-docs.deepseek.com/zh-cn/api/get-user-balance/)。调用响应的 Token usage 可作单次调用计量来源，但不能代替账户实际扣款记录；官方价格页也说明价格可能变动。[官方 Token 用量说明](https://api-docs.deepseek.com/zh-cn/quick_start/token_usage/)、[官方模型与价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)。因此，本公开资料范围内尚无可供 SkillShift 程序按请求拉取账单的已文档化接口证据；控制台是否支持人工费用明细导出、按 API Key/项目分账及发票取得方式，仍需在未来获批账号内只读核验。

建议分层：本地持久预算账本继续作为“是否可再发请求”的唯一硬门；Provider usage 与版本化价格只形成逐请求估算/交叉核验；账户余额快照只作为余额健康信号。余额差额可能混有充值、赠金过期或同账户其他服务用量，不能单独归因到 SkillShift；若不能取得可复核的账户级明细，应使用专用项目账号并由费用责任人按账单人工月结，否则不得以 100 元“项目月上限”名义真实启用。遇到价格快照过期、币种/汇率未定义、实际模型 ID 未批准、响应 usage 缺失或账单差异时，默认拒绝新调用或进入待对账，不自动释放预算。

本研究发现时，Usage Boundary 已新增 16,384 UTF-8 字节总输入上限、600 输出 Token 上限及响应 usage 严格解析/本地估算契约；旧报告第 3 节第 1 项“输入无硬上限”及第 5 节的首条待实现建议属于修正前状态快照，不是当前代码状态。输入 Token 最坏值仍未由官方 tokenizer 或真实 usage 证明，单次预算预留与 Provider 调用尚未生产化集成，故 PCP-17 仍部分完成。

验证范围：仅阅读当前公开官方文档和本地代码/测试 Artifact；未访问账号、发起 API 请求、使用 Key、连接 ECS或生成费用。价格与 API 能力均为 2026-09-24 查询快照，正式接入前需复核。

## 实际执行命令与结果

```text
Get-Content -LiteralPath 'apps\agent-first\agent_first\deepseek_contract.py' -Raw -Encoding utf8
Get-Content -LiteralPath 'apps\agent-first\agent_first\deepseek_runtime.py' -Raw -Encoding utf8
Get-Content -LiteralPath 'apps\agent-first\agent_first\school_budget.py' -Raw -Encoding utf8
Get-Content -LiteralPath 'apps\agent-first\agent_first\synthetic_budget_ledger.py' -Raw -Encoding utf8
  -> 确认输入无硬上限；输出有 600 Token 上限；响应 usage/model 与 settle 未进入当前接缝
官方资料检索：DeepSeek API 官方中文价格、V4.1-Flash 发布、Token 用量和 Chat Completions 文档
  -> 确认当前单价/峰谷时段/响应用量字段；没有验证私有账号账单 API
git diff --check
  -> PASS（仅本地文本差异检查；本报告不含运行测试）
```

没有运行测试，因为本任务只读研究；没有调用 API、登录供应商账号、使用凭据、连接 ECS、使用真实数据或产生费用。

## Artifact 与 SHA-256

| 文件 | SHA-256 |
| --- | --- |
| `specs/R0-DEEPSEEK-BUDGET-RECONCILIATION-RESEARCH/README.md` | `32B0554F500E333964AB51F2B418DEE951E2C2B40AACCB1FCF0894ECEA0D8397` |
| `artifacts/R0-PRODUCTION-CONTROL-PLANE-READINESS/READINESS_CHECKLIST_2026-09-24.md` | `45CEA2130794BB582D88C21CF5B46BE40141AE89EADA2C45552DC66DE56DF509` |
| `artifacts/R0-PRODUCTION-CONTROL-PLANE-READINESS/READINESS_REPORT_2026-09-24.md` | `C818EE41BBCEA746818AD97FB7D1F6E5606F812CA451EB4901C80BCC7870D56D` |
| `docs/CURRENT_STATE.md` | `1654104E6EDE7172B1FCED739A33B6B91AF414CAD6F32BCE696800AD6685472B` |
| `docs/README.md` | `A6EA8936D027D86FB13B99E25499F80541F2764A6B3AF7381268E8D2062CE394` |

本报告自身 SHA-256 在最终状态回报中给出，避免自引用。

## Git diff 摘要

- 新增研究规格与报告；更新 PCP-17 清单状态和入口/当前状态记录，并追加就绪报告当前快照。
- 不改运行时代码、模型选择、价格合同或预算硬上限；未执行删除、重置、清理、提交、推送或部署。

## Commit

`NONE`
