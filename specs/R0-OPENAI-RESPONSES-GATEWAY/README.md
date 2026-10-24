# R0-OPENAI-RESPONSES-GATEWAY：Gate B 模型网关准备

## 状态

- Task ID：`R0-OPENAI-RESPONSES-GATEWAY-001`
- 类型：FEATURE / 模型网关准备
- 状态：**Superseded / Historical（2026-09-24）**；项目负责人已明确不使用 OpenAI API。无密钥、无网络的契约和失败安全测试保留为历史证据；真实 Responses API 调用从未进行，也不再计划。
- 上游：ADR-005、`docs/product/R0_AGENT_FIRST_DELIVERY_DECISION.md`、`docs/product/REQUIREMENTS_SPEC.md`。

## 目标

为 OpenAI Responses 服务端网关建立最小、可测试且无密钥的接口：版本化模型配置、请求约束、`store: false`、无配置时的明确失败，以及对教学闭环的可恢复影响。

## 允许范围

- 不含密钥的 OpenAI Responses 请求结构和错误状态；
- 适配器接口抽象、确定性 fake response 的契约测试；
- 仅使用合成任务、合成身份和本地测试；
- ADR、质量规则和 Artifact。

## 禁止范围

- 真实 API 调用、账号创建、计费、密钥请求、密钥写入、SDK 安装或网络探测；
- 真实学生/教师数据、真实作业、部署、ECS 连接、模型工具调用或本机自动化；
- 自动评分、作弊判断、能力结论或将失败伪装为模型回答。

## 验收

| ID | 条件 | 最小证据 |
| --- | --- | --- |
| OG-01 | ADR 明确服务端密钥、`store: false`、无工具和 synthetic-only 边界。 | ADR-005 审阅。 |
| OG-02 | 配置缺失时适配器失败为 `MODEL_UNAVAILABLE`，不生成虚构指导。 | unit test。 |
| OG-03 | 请求只包含版本化 allowlisted model、任务输入和 `store: false`；学生不能控制 model 或工具。 | unit test。 |
| OG-04 | 密钥不会进入配置对象、事件、错误文本、Manifest 或 Artifact。 | unit/negative test。 |
| OG-05 | 真实调用的前置：负责人配置专用服务端 key、设置预算保护并授权一次合成 probe。 | BLOCKED，运行前检查。 |

## 停止条件

需要真实 key、费用、外网调用、真实数据、部署、工具调用或学生身份时停止并转入独立授权步骤。不要让用户在聊天中发送 key。
