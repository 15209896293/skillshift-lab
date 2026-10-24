# R0-DEEPSEEK-HOSTED-SYNTHETIC-RUNTIME：托管合成运行时接缝

## 状态

- Task ID：`R0-DEEPSEEK-HOSTED-SYNTHETIC-RUNTIME-001`
- 类型：FEATURE / Gate B 运行时安全接缝
- 状态：**Implemented / Verified（假传输层；无真实 Key、无网络、无费用）**。
- 上游：ADR-006、ADR-007、ADR-008。

## 目标

为已授权的“学校统一付费 DeepSeek 托管合成探针”建立默认拒绝的服务端运行时契约。只有未来服务端同时提供预算许可和凭据解析，才允许调用固定 DeepSeek 目标；本规格不执行实际调用。

## 允许范围

- 服务端凭据解析、预算许可和 JSON 传输的 Protocol；
- 固定 DeepSeek 官方目标和 ADR-007 请求 payload；
- 合成数据分类检查、30 秒以内的超时边界、异常响应失败关闭；
- 使用假对象的单元测试。

## 禁止范围

- 真实 Key、HTTP 客户端、环境变量、数据库、凭据库、预算扣费实现、部署或 ECS 连接；
- 未许可调用、真实学生或教师内容、RAG、工具、联网搜索、其他供应商切换；
- 将模型响应作为成绩、作弊或能力结论，或让其改变教师复核状态。

## 验收

| ID | 条件 | 最小证据 |
| --- | --- | --- |
| DSR-01 | 默认/拒绝许可时，不解析凭据、不调用传输层，返回 `MODEL_UNAVAILABLE`。 | unit test。 |
| DSR-02 | 缺失/撤销凭据时，不调用传输层，错误不泄露凭据引用。 | unit test。 |
| DSR-03 | 获许可的合成请求仅访问固定目标，payload 无 tools、user ID 或凭据。 | fake-transport test。 |
| DSR-04 | 畸形响应没有伪造指导，返回可见不可用状态。 | negative test。 |

## 停止条件

若需要真实 Key、真实费用、真实网络、预算额度、部署、身份/租户、真实数据或任何额外模型能力，停止在本规格范围内推进。先完成 ADR-008 第 5 条运行时配置记录和独立合成探针授权。

