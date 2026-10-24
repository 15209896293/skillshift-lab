# Gate B 国内教育智能体模型路线研究报告

## Task ID 与结论

- Task ID：`GATE-B-DOMESTIC-MODEL-RESEARCH-001`
- Gate：B
- 结论：**PARTIAL / Proposed**。OpenAI API 路线已由项目负责人否决；已完成公开资料研究和可替换网关建议，但尚未决定国内供应商、模型、托管/本地化部署、费用或真实调用。

## 可核验事实

- 科大讯飞公开以星火大模型及科学专有模型支撑其 AI 科学教育。
- 好未来公开其九章大模型（MathGPT），并披露“随时问”融合 DeepSeek R1。
- 网易有道公开以“子曰”教育大模型覆盖教育场景，但未披露具体底座或部署细节。
- 希沃公开自研教学大模型（备案名 CVTE 大模型）、教育 RAG/知识图谱/向量数据库、学校本地化 DeepSeek 接入，以及自研教育模型与 DeepSeek、豆包、Kimi 的混合架构。
- 作业帮官方资质页仅披露 AI 功能由银河大模型支持。

完整来源、证据边界和推荐见 `../../docs/product/DOMESTIC_EDUCATION_AGENT_MODEL_ROUTE_RESEARCH.md`。

## 对产品的建议

**Proposed：** 保持平台服务端统一 Model Gateway，学生不配置模型或 Key；模型档案需集中记录供应商、部署方式、模型/提示词版本、教育资源/RAG 版本、工具策略、数据类别、配额和失败回退。

应在“国内托管模型网关”与“学校本地化模型网关”中选择一条先验证。DeepSeek R1 是国内教育产品公开采用的候选，不是已确认的 SkillShift 模型。

## 文件变化

| 文件 | 原因 |
| --- | --- |
| `docs/product/DOMESTIC_EDUCATION_AGENT_MODEL_ROUTE_RESEARCH.md` | 记录公开样本、不可推断边界和 Proposed 路线。 |
| ADR-005、`specs/R0-OPENAI-RESPONSES-GATEWAY/`、OpenAI 报告 | 标为 Superseded/Historical，保留未发生真实调用的可审计记录。 |
| `README.md`、`docs/README.md`、需求/技术/质量/状态/交接文件 | 清除 OpenAI 作为活动路线的表述。 |
| `apps/agent-first/agent_first/__init__.py` | 停止导出 OpenAI 历史适配器；它不再属于活动运行入口。 |

## 实际验证

| 命令 | 结果 |
| --- | --- |
| `python -B -m unittest discover -s tests -p 'test_agent_first_vertical_slice.py' -v` | PASS，7 tests。 |
| `python -B -m unittest discover -s tests -p 'test_openai_gateway_contract.py' -v` | PASS，4 个历史无网络契约测试；未调用 OpenAI。 |
| 活动 OpenAI 路线文本检查 | PASS，无活动声明；仅保留明确标注为历史/否决的记录。 |
| `git diff --check` | PASS。 |

## 证据

```text
7C5183B686EB0BD8C6061E683C69A7D6581ECDE88D1AF17A09B5A93E0B5A9984  docs/product/DOMESTIC_EDUCATION_AGENT_MODEL_ROUTE_RESEARCH.md
```

## 已知限制与下一步

- 公开产品页面不披露其完整 API、Key、数据治理、提示词、路由与成本方案；不得补写为项目事实。
- 还没有确定任何国内模型供应商、费用或部署，因此不得进行真实请求。
- 下一步需要项目负责人选择先验证国内托管路线还是学校本地化路线；选择后才创建供应商专属规格。

## Git

- Commit：`NONE`。
- 未删除、重置、推送或部署任何内容。

