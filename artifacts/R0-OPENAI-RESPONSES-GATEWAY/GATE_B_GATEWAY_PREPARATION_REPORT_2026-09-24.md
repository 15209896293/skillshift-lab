# Gate B：OpenAI Responses 网关准备报告

> **历史状态更新（2026-09-24）：** 项目负责人已明确不使用 OpenAI API。本报告记录的是未发生真实调用的准备工作，不能作为当前模型路线、部署或供应商决定；不删除以保留可审计事实。

## Task ID 与状态

- Task ID：`R0-OPENAI-RESPONSES-GATEWAY-001`
- Gate：B（真实教育 Agent 模型路线）
- 结论：**PARTIAL**。OpenAI 服务端网关路线、无密钥请求契约和失败安全行为已验证；真实 OpenAI API 调用尚未授权或执行。

## 已确认路线

项目负责人已授权 OpenAI 作为真实教育 Agent 的服务端模型路线。ADR-005 将调用限定为 OpenAI Responses API、服务端专用密钥、冻结合成任务、`store: false`、无工具调用和明确失败状态。学生客户端不持有密钥，模型不能自动评分、判定作弊、建立能力结论或执行本机工具。

官方依据：OpenAI 的 [Production best practices](https://developers.openai.com/api/docs/guides/production-best-practices) 要求不要在代码或公开仓库暴露 API key，并建议用环境变量或密钥管理服务、设置 key 生命周期与用量保护；[Responses migration guidance](https://developers.openai.com/api/docs/guides/migrate-to-responses) 说明 Responses 默认会保存状态，`store: false` 可禁用该状态保存。

## 文件变化

| 文件 | 原因 |
| --- | --- |
| `docs/adr/ADR-005-openai-responses-server-gateway.md` | 写入服务端网关、数据、密钥、工具和失败边界。 |
| `specs/R0-OPENAI-RESPONSES-GATEWAY/README.md` | 明确 Gate B 的允许范围、禁止范围、验收和停止条件。 |
| `apps/agent-first/agent_first/openai_gateway.py` | 无网络的请求形状和 `MODEL_UNAVAILABLE` 失败安全实现。 |
| `apps/agent-first/agent_first/scripted_guidance.py`、`domain.py` | 抽取通用 Guidance Adapter 契约，不改变 Gate A 确定性行为。 |
| `tests/test_openai_gateway_contract.py` | 验证 `store: false`、无工具、无密钥字段、学生不能选模型以及失败安全。 |

## 实际执行命令与结果

| 命令 | 结果 |
| --- | --- |
| `python -B -m py_compile ... openai_gateway.py ... test_openai_gateway_contract.py` | PASS。 |
| `python -B -m unittest discover -s tests -p 'test_agent_first_vertical_slice.py' -v` | PASS，7 tests。 |
| `python -B -m unittest discover -s tests -p 'test_openai_gateway_contract.py' -v` | PASS，4 tests。 |
| 静态 import 检查 | PASS；网关契约没有 `requests`、`urllib`、`http`、`socket` 或 `openai` SDK 导入。 |
| `git diff --check` | PASS。 |

## 可复核哈希

```text
F24C78B7BE7B53B4F1D9568405A486075C31ADE10E21C1DEBD1B67D708008AEA  docs/adr/ADR-005-openai-responses-server-gateway.md
989A3564F1615495DD55F7AD09CB5DE842F746E3B892DC8DCFCCD400A5862C95  specs/R0-OPENAI-RESPONSES-GATEWAY/README.md
CC0F77DD3FBA6B2F6B1CFBBD617EBF07DB756A90AF6F6BD0F453BFAA3ECC67EB  apps/agent-first/agent_first/openai_gateway.py
B0C593F48FA34D861518AEC88E16B8F9FD9943C5066906A068AB64B30D80D7ED  tests/test_openai_gateway_contract.py
```

## 已知限制与风险

- 没有真实 API key、网络请求、模型输出、费用、真实学生数据或部署证据；不能宣称模型已经可用。
- 当前 model ID 仍是服务端 allowlist 契约，不是经成本/质量评估冻结的生产模型选择。
- `store: false` 是请求级要求，不替代对真实数据、保留、授权和学校制度的独立治理。
- 当前 ECS 不参与本任务，且仍不得运行任意学生代码。

## 下一步与停止条件

真实调用前需要项目负责人自行在受控服务端创建专用、可轮换且有预算保护的项目 key，并明确授权一次仅含冻结合成内容的 Responses probe。不要在聊天中发送 key。未满足前，Gate B 保持 PARTIAL，系统继续使用 Gate A 的确定性适配器。

## Git

- Commit：`NONE`。
- 未提交内容包含既有材料与本 Gate 新增文件；本任务未删除、重置、推送或部署。
