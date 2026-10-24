# ADR-008 DeepSeek 托管合成运行时授权

## Status

Accepted（2026-09-24；项目负责人授权学校统一付费的 DeepSeek 官方托管 API，但当前未发生真实调用）。

## Context

项目负责人已确认：首条真实模型路线使用学校统一付费的 DeepSeek 官方托管 API，且第一阶段只发送冻结合成任务文本。ADR-007 已固定 `deepseek-flash`、关闭思考、600 Token 上限与无工具请求。

真实调用将产生费用和数据传输风险。当前项目没有身份/租户服务、凭据库、预算服务或部署环境；任何将 Key 写入学生端、源代码、配置读取接口、日志或 Artifact 的做法均违反项目边界。

## Decision

1. 允许为 DeepSeek 建立服务端运行时接缝，但默认拒绝所有真实调用。运行时必须同时获得：
   - 学校服务端凭据引用对应的短生命周期密钥解析结果；
   - 已由未来原子预算/授权服务发放的合成探针许可。
2. 缺少许可、预算、凭据、合成数据分类或有效响应时，一律在传输前/后返回可见的 `MODEL_UNAVAILABLE`；不得回退到另一外部供应商。
3. 初始托管目标固定为 DeepSeek 官方 `https://api.deepseek.com/chat/completions`；请求仅使用 ADR-007 的受限 payload。使用兼容 Chat Completions 格式不代表使用 OpenAI 服务。
4. 凭据解析器、预算许可和 JSON 传输层均以服务端注入接口表示。代码库不实现默认 HTTP 客户端、环境变量读取、明文 Key、数据库保存或部署脚本；测试只能使用假凭据、假许可和假传输层。
5. 项目负责人已确认首轮合成探针的学校费用硬上限为 **100 元/月**。任何未来预算许可服务必须在发出请求前原子预留额度，达到上限后拒绝请求并返回 `MODEL_UNAVAILABLE`。当前没有预算许可服务，因此默认拒绝。
6. 真实探针前仍需补充一份不含 Key 的运行时配置记录：学校费用所有者、供应商账户权限、数据保留条款、密钥轮换/撤销、访问者、告警、失败处理、价格版本和合成任务版本。

## Consequences

- 当前可以单元测试“未许可绝不出网、无凭据绝不出网、payload 固定、异常响应不伪造指导”。
- 当前不能声称 DeepSeek 已连通、成本已验证、模型质量已验证或 API Key 已安全运营。
- 真实学生、教师资料、RAG、联网搜索、工具、流式长对话、本机代码执行和正式部署仍被禁止。

## Evidence

- [DeepSeek 首次调用 API](https://api-docs.deepseek.com/zh-cn/)：官方 base URL、`deepseek-flash` 与 `/chat/completions` 用法。
- ADR-006、ADR-007。
- `../../apps/agent-first/agent_first/deepseek_runtime.py`
- `../../tests/test_deepseek_runtime_contract.py`
