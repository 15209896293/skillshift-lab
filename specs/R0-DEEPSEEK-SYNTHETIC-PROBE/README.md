# R0-DEEPSEEK-SYNTHETIC-PROBE：DeepSeek 合成探针契约

## 状态

- Task ID：`R0-DEEPSEEK-SYNTHETIC-PROBE-001`
- 类型：FEATURE / Gate B 供应商契约
- 状态：**Implemented / Verified（仅限无网络、无真实 Key 的请求约束与失败关闭）**。
- 上游：ADR-006、ADR-007、`specs/R0-DOMESTIC-MULTI-MODEL-GATEWAY/README.md`。

## 目标

把项目负责人选择的 DeepSeek 固化为首个学校统一管理的合成探针配置，并验证请求不会打开思考、工具、联网搜索、流式输出、任意模型切换或学生隐私标识。

## 允许范围

- `deepseek-flash` 的固定模型档案；
- DeepSeek Chat Completions 兼容的本地请求结构；
- `thinking.type=disabled`、最大输出 600 Token、无工具、无 `user_id`；
- 所有消息内容总计最多 16,384 UTF-8 字节；该本机探针上限不代表课堂可用长度；
- 托管合成运行时要求响应包含一致的 request ID、模型 ID、prompt/completion/total Token 与缓存命中 Token；缺失或矛盾即失败关闭；
- 类型化 usage 与基于显式价格快照的估算仅留运行时内存，不进入提交 Manifest；估算不是账单结算；
- 失败关闭、单元测试和本地 Artifact。

## 禁止范围

- endpoint、HTTP/SDK、真实 Key、真实网络调用、费用、部署或 ECS 连接；
- `deepseek-v4-pro`、任意模型 ID、教师 BYOK 的真实调用、学生模型配置；
- 真实学生/教师数据、RAG、联网搜索、工具调用、自动评分、作弊/能力判断。

## 验收

| ID | 条件 | 最小证据 |
| --- | --- | --- |
| DSP-01 | 首个档案只能是学校管理的 DeepSeek `deepseek-flash`，且不含明文 Key。 | unit test。 |
| DSP-02 | 请求只有任务范围的 system/user 消息，关闭思考，最大输出不超过 600，且非流式。 | unit test。 |
| DSP-03 | 请求不含 tools、tool choice、user ID、endpoint 或凭据。 | negative test。 |
| DSP-04 | 错误 provider/model/输出上限均被拒绝；未授权调用为 `MODEL_UNAVAILABLE`。 | unit test。 |
| DSP-05 | 输入 UTF-8 字节超限拒绝且不回显内容；供应商 usage 缺失/矛盾时失败关闭。 | contract/runtime tests。 |
| DSP-06 | Manifest 不含 request ID、usage Token 或费用估算；假响应可严格复核。 | vertical-slice/runtime tests。 |

## 停止条件

需要真实 Key、费用、网络、真实数据、教师 BYOK 调用、部署或任何工具调用时，停止在本规格范围内推进。进入 ADR-007 第 5 条的独立授权与运行时验证。

## 实施证据

- 代码：`../../apps/agent-first/agent_first/deepseek_contract.py`
- 测试：`../../tests/test_deepseek_contract.py`
- 报告：`../../artifacts/R0-DEEPSEEK-SYNTHETIC-PROBE/DEEPSEEK_CONTRACT_REPORT_2026-09-24.md`
