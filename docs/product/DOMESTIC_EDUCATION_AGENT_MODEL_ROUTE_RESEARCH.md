# 国内教育智能体的模型路线研究

## 状态与效力

- 状态：**Proposed research**（2026-09-24）。
- 目的：回答国内教育智能体公开采用哪些模型/部署模式，并为 SkillShift Gate B 提供证据边界。
- 非结论：本文件不代表已选定供应商、模型、费用、部署方式、数据合规方案或真实模型能力。
- 当前决定：OpenAI API 已被项目负责人否决；ADR-005 仅保留历史记录。

## 1. 公开可核验的样本

| 产品/厂商 | 公开披露的模型或能力 | 对 SkillShift 的可用启示 | 不可推断 |
| --- | --- | --- | --- |
| 科大讯飞 AI 科学教育 | 依托讯飞星火大模型；科学探究场景还称使用“科学专有大模型”、虚拟科学家、专有资源库与过程数据。 | 模型不是学生自行配置，而是被封装在任务、资源和教学工作流内。 | 未公开说明其底层模型、学校数据路径或 API 细节。 |
| 好未来 / 学而思 | 九章大模型（MathGPT）是自研教育模型；公开页面还说明“随时问”深度融合 DeepSeek R1。 | 教育产品可把自研教育能力与通用推理模型组合，而不是只有单一基座模型。 | 未公开其路由、提示词、数据隔离、Key 管理或成本控制细节。 |
| 网易有道智慧教育 | 公开使用“子曰”教育大模型，覆盖教、学、管、评、服等教育场景。 | 教育产品将模型作为平台能力而非由学生输入模型配置。 | 未公开“子曰”的具体底座、部署方式或外部模型组合。 |
| 希沃教学大模型 | 备案名为 CVTE 大模型；公开说明端侧算力、教育 RAG、知识图谱/向量数据库，并称可接入学校本地部署的 DeepSeek；还披露自研教育模型与 DeepSeek、豆包、Kimi 等形成混合架构。 | 最接近可复用工程模式：**统一模型网关 + 教育资源/RAG + 多模型路由 + 可选学校本地化部署**。 | 不能据此断言 SkillShift 已具备本地算力、RAG 质量或学校数据不出域能力。 |
| 作业帮 | 官方资质页面称其 AI 功能由银河大模型支持。 | 说明垂直教育产品常以自有模型品牌封装能力。 | 该页面不披露模型配置或部署架构。 |

来源：

- [科大讯飞 AI 科学教育](https://edu.iflytek.com/solution/school/ai-science-education)
- [好未来：学习机与九章大模型](https://www.tal.com/zh-cn/news/detail/3028)；[好未来：随时问与 DeepSeek R1](https://www.tal.com/zh-cn/homepage/22)
- [有道智慧教育](https://zhihui.youdao.com/)
- [希沃教学大模型](https://www.seewo.com/product/detail/AI)；[希沃接入学校本地化 DeepSeek](https://www.seewo.com/article/detail/2700)；[希沃混合模型架构与 RAG](https://www.seewo.com/article/detail/2733)
- [作业帮资质页](https://base-vue.zuoyebang.com/static/hy/base-vue/license-new.html?showkey=business)

## 2. 研究结论

从以上公开资料可作出一个有限推断：国内教育产品的共同做法不是让每名学生配置 LLM 或保管 API Key，而是由产品/学校侧统一配置模型能力，再把它置于课程资源、学科知识、任务流程、教师控制与数据治理边界之内。

它们使用的模型并不统一：星火、九章（MathGPT）/DeepSeek R1、子曰、希沃教学大模型（CVTE）与银河大模型都存在。没有公开资料能证明某一个模型天然最适合 SkillShift；模型本身也不能替代教师复核、学生验证或隐私设计。

## 3. 对 SkillShift 的 Proposed 路线

本节的公开研究结论不等于供应商决定。其后，项目负责人已通过 ADR-006 确认多模型网关与凭据边界，并通过 ADR-007 选择 DeepSeek `deepseek-flash` 作为首个**无网络合成探针**的模型标识。该选择不改变本研究的证据边界，也不表示 DeepSeek R1、真实调用、费用、数据路径或学校本地部署已经确定。

SkillShift 应保留目前的 `GuidanceAdapter` 契约，并在其后设置**学校/平台统一的 Model Gateway**，而不是向学生客户端下发模型 Key。每个可审计的模型档案至少应包含：

```text
provider / deployment mode / model ID and version / task prompt version
education-resource or RAG corpus version / allowed tools = none by default
data classification / quota and cost owner / failure and fallback policy
```

建议比较两条国内路线，而不是现在就接入任意 API：

1. **国内托管模型网关**：由平台服务端集中保管供应商凭据，适合快速完成合成任务验证；需另行确认费用、数据出域与可用性。
2. **学校本地化模型网关**：类似希沃公开的“学校本地部署 DeepSeek”方式；更利于把学校数据留在本地，但需要独立核验算力、运维、模型许可和安全更新。

DeepSeek R1 是有国内教育产品公开采用的候选。SkillShift 当前已确认的仅是 ADR-007 中 `deepseek-flash` 的无网络合成探针契约；R1、其他模型和任何真实部署仍未确认。

## 4. 下一项需要项目负责人决定的事项

首个供应商已选择 DeepSeek；在实现任何国内真实模型调用前，仍须选择：先验证“国内托管模型网关”，还是投入“学校本地化模型网关”，并确认费用所有者、数据路径/保留和运行时授权。这会实质改变费用、网络、硬件、运维和数据路径，不能由研究报告自行替代决定。
