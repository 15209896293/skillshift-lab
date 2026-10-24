# R0-DOMESTIC-MULTI-MODEL-GATEWAY：国产多模型网关契约

## 状态

- Task ID：`R0-DOMESTIC-MULTI-MODEL-GATEWAY-001`
- 类型：FEATURE / Gate B 本地契约
- 状态：**Implemented / Verified（仅限无网络、无真实密钥、合成任务的网关配置与降级契约）**。
- 上游：ADR-006、`docs/product/R0_AGENT_FIRST_DELIVERY_DECISION.md`、`docs/product/REQUIREMENTS_SPEC.md`、`docs/architecture/TECHNICAL_SPEC.md`、`docs/quality/QUALITY_SPEC.md`。

## 目标

在不调用真实模型的前提下，为国产多模型路线建立最小、可替换、可测试的服务端网关契约：学校统一模型档位、教师可选 BYOK 的凭据引用、学生无 Key，以及模型不可用时的明确固定引导降级。

## 允许范围

- 固定的国产 provider 标识与模型档案；
- 不含明文密钥、URL 或 SDK 的 `ModelProfile`；
- 任务范围请求形状、默认无工具/无联网搜索、`MODEL_UNAVAILABLE` 失败关闭；
- 使用确定性适配器的可见降级、事件和 Manifest 记录；
- 合成单元/集成测试与本地 Artifact。

## 禁止范围

- 真实 API Key、账户、充值、厂商 SDK、真实网络请求、部署或 ECS 连接；
- 教师配置页面、身份、租户、数据库、凭据库、预算服务或真实 BYOK 保存；
- 学生配置 provider/model/endpoint/key/工具/预算，或任意自定义 endpoint；
- 真实学生或教师数据、真实作业、RAG、联网搜索、本机代码执行；
- 自动评分、作弊判断、能力结论、模型输出直接关闭作业或静默外部模型切换。

## 领域契约

```text
Server-owned ModelProfile
    provider + model/version + prompt version + data classification
    + access mode + credential reference only + tools/web search disabled
        ↓
DomesticModelGatewayAdapter
    bounded task request → MODEL_UNAVAILABLE (until live authorization)
        ↓
FallbackGuidanceAdapter
    visible deterministic guidance + fallback record in event/manifest
```

访问模式：

| 模式 | 允许的所有者 | 当前含义 |
| --- | --- | --- |
| `platform_basic` | 平台/学校 | 只允许确定性基础降级；不是永久免费外部模型承诺。 |
| `school_managed` | 未来学校管理员 | 需服务端凭据引用；当前无运行时。 |
| `teacher_byok` | 未来教师本人 | 需服务端凭据引用；学生无法查看或配置。 |
| `school_local` | 未来学校管理员 | 不携带外部 provider 凭据；本地模型节点另需部署决定。 |

## 验收

| ID | 条件 | 最小证据 |
| --- | --- | --- |
| DMG-01 | 档案只接受预置国产 provider；无任意 URL、模型工具或联网搜索配置。 | unit test。 |
| DMG-02 | 档案不包含明文 API Key/secret；托管/BYOK 模式只能引用服务端凭据标识。 | unit/serialization test。 |
| DMG-03 | 学生问题不能覆盖 server-owned provider、模型或工具策略。 | unit test。 |
| DMG-04 | 未授权运行时显式失败为 `MODEL_UNAVAILABLE`，不伪造模型回答。 | unit test。 |
| DMG-05 | 固定引导降级可见，并在事件/Manifest 中记录来源、可用性和回退版本。 | integration test。 |
| DMG-06 | Manifest、错误文本与序列化数据不含明文密钥、凭据引用、作弊或能力结论。 | negative test。 |

## 停止条件

出现真实 Key、供应商账户、费用、外网调用、真实数据、身份/租户、部署、RAG、联网搜索或本机执行需求时，停止在本规格范围内扩大实现。转入 ADR-006 第 6 条规定的独立运行时决定与验证。

## 实施证据

- 代码：`../../apps/agent-first/agent_first/model_gateway.py`
- 测试：`../../tests/test_domestic_model_gateway_contract.py`
- 报告：`../../artifacts/R0-DOMESTIC-MULTI-MODEL-GATEWAY/GATE_B_CONTRACT_REPORT_2026-09-24.md`

