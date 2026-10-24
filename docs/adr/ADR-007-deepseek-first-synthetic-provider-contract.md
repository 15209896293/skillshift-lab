# ADR-007 DeepSeek 首个合成探针供应商契约

## Status

Accepted（2026-09-24；仅确认首个供应商与无网络请求契约）。

## Context

项目负责人已选择 DeepSeek 作为 SkillShift 首个国产模型供应商。ADR-006 已先确认多模型网关、学校统一档位、教师可选 BYOK、学生无 Key 和可见基础降级的共同边界。

DeepSeek 当前官方 Chat Completions 文档列出 `deepseek-flash` 与 `deepseek-v4-pro`，并允许显式关闭思考模式、设置输出上限和不传工具。首条教学合成探针优先验证低成本、短文本、无工具的任务内引导，而不是复杂推理、浏览器 Agent、文件处理或自动化。

## Decision

1. 首个未来真实合成探针的 provider 为 DeepSeek，访问模式固定为学校统一管理；教师 BYOK 保持 ADR-006 中的后续可选能力，暂不启用真实调用。
2. 无网络契约的 allowlisted model ID 为 `deepseek-flash`。`deepseek-v4-pro` 及其他模型不是本探针的可选项；如需调整，必须以新的模型档案和合成验证记录说明原因。
3. 请求固定为：两条任务范围消息、`thinking.type = disabled`、`max_tokens <= 600`、非流式、不传 `tools`、`tool_choice` 或 `user_id`。不传 `user_id` 是为了避免在供应商请求中引入学生隐私标识。
4. 代码仅构造请求形状并在调用处失败为 `MODEL_UNAVAILABLE`；不含 endpoint、HTTP 客户端、SDK、Key 或真实网络调用。
5. 若未来启用真实探针，只可使用冻结合成任务与学校服务端凭据；必须先记录费用所有者、硬预算、数据路径/保留条款、凭据保管和撤销策略，并经独立授权。学生数据、真实教师资料、课程 RAG、联网搜索、工具调用和部署仍不在本 ADR 范围内。

## Consequences

- 平台可以验证 DeepSeek 特有请求的模型、思考、Token、工具和隐私字段是否被固定，而不产生模型费用。
- `deepseek-flash` 是探针配置标识，不是已经运行或质量通过的模型版本承诺；DeepSeek 未来模型更新、定价和能力变化需要重新核验。
- 使用兼容的 Chat Completions 请求形状不等于使用 OpenAI 服务；ADR-005 仍为已否决的历史记录。

## Evidence

- [DeepSeek Chat Completions API](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion/)：模型 ID、thinking、输出上限、工具与 `user_id` 字段。
- 实施规格：`../../specs/R0-DEEPSEEK-SYNTHETIC-PROBE/README.md`
- 本地测试与报告：`../../tests/test_deepseek_contract.py`、`../../artifacts/R0-DEEPSEEK-SYNTHETIC-PROBE/`

