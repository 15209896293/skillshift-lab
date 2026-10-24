# ADR-006 国内多模型网关与凭据边界

## Status

Accepted（2026-09-24；仅确认 R0 Gate B 的产品与本地契约边界）。

## Context

项目负责人已确认：SkillShift 应预留国产模型接入；学校可统一配置模型服务，教师可选择配置自己的模型凭据，学生只使用学校开放的模型档位且绝不获得或配置 API Key。

该决定不等于选定供应商、开通账户、购买额度、部署服务端、存储真实凭据、发起网络请求或处理真实学生数据。当前 Gate A 已验证的只是确定性合成工作流。外部“免费模型”或免费网页版不能被承诺为永久、无限、稳定的生产 API；开源本地模型也仍有计算与运维成本。

## Decision

1. R0 采用服务端导向的、可替换的国内 `Model Gateway`。它与教学 Agent 编排分离：模型只生成任务内引导，不能评分、判定作弊、推断能力或自行改变教师复核状态。
2. 模型访问角色固定如下：
   - 学生只能使用课程/学校已开放的模型档位，不得提交或查看 provider、model ID、endpoint、工具策略、预算或 API Key。
   - 学校管理员在未来身份与租户服务完成后，管理学校统一模型档位、凭据引用、课程范围和预算。
   - 教师可选 BYOK；真实凭据只能进入经授权的服务端凭据库，配置读取接口、事件、提交包、日志、错误和 Artifact 均只能出现凭据引用，绝不出现明文。
3. 初始可配置 provider 标识为 `deepseek`、`qwen`、`doubao`、`zhipu`、`kimi` 与 `school_local`。这是允许列表，不表示任一供应商、模型版本、价格、数据保留条款或部署方式已选定。学生、教师和任务文本都不能填写任意 URL。
4. Gate B 的基础档位不是“永久免费的第三方 API”承诺。当前实现只允许确定性、零外部调用的可见降级；未来基础语言服务可以来自学校统一额度或经独立验证的本地模型节点。额度耗尽或模型不可用时，系统必须显式显示 `MODEL_UNAVAILABLE` 或固定引导降级，不得静默切换到另一外部供应商。
5. 所有 Gate B 模型档案必须版本化记录：provider、model ID/version、prompt version、数据分类、访问模式、凭据引用、成本所有者、预算、回退策略和允许工具。默认 `tools = none`、联网搜索关闭；任务材料仅限最小必要的合成文本。
6. 本 ADR 授权的工程范围仅为无网络、无真实密钥的本地契约、适配器、测试和 Artifact。真实调用前仍必须完成供应商/数据保留/费用/部署的项目负责人决定，以及服务端身份、租户、凭据保管、配额、审计和合成探针验证。

## Consequences

- 可以在不产生费用、不接触敏感数据的前提下，验证模型档案、白名单、失败关闭和可见降级是否被工作流正确记录。
- 当前确定性 `ScriptedGuidanceAdapter` 保留为唯一已验证的基础降级；它不是 LLM，也不得被描述为真实模型能力。
- 真实 BYOK UI、凭据库、课程授权、预算服务、供应商 SDK/API、RAG、联网搜索、本地模型进程和部署均不在本 ADR 的实施范围。
- 自定义 endpoint 被拒绝；若以后要支持校内模型节点，必须由学校管理员在独立部署决定中配置，不开放给学生或教师任意输入。

## Evidence and acceptance boundary

- 实施规格：`../../specs/R0-DOMESTIC-MULTI-MODEL-GATEWAY/README.md`
- Gate A 边界：ADR-004、`../product/R0_AGENT_FIRST_DELIVERY_DECISION.md`
- 国内路线研究：`../product/DOMESTIC_EDUCATION_AGENT_MODEL_ROUTE_RESEARCH.md`
- 本地测试与报告：`../../tests/test_domestic_model_gateway_contract.py`、`../../artifacts/R0-DOMESTIC-MULTI-MODEL-GATEWAY/`

