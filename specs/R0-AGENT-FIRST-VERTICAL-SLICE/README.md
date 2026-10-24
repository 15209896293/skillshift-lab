# R0-AGENT-FIRST-VERTICAL-SLICE：教育 Agent 教学闭环

## 状态

- Task ID：`R0-AGENT-FIRST-VERTICAL-SLICE-001`
- 类型：FEATURE / 合成产品闭环
- 状态：**Implemented / Verified（2026-09-24；仅限确定性、合成、无外部模型与无本机自动执行范围）**。
- 上游：`docs/product/R0_AGENT_FIRST_DELIVERY_DECISION.md`、ADR-004、`docs/product/REQUIREMENTS_SPEC.md`。

## 目标

以一项冻结的合成教学任务，验证下列系统闭环可被实现和复核：教师创建任务，学生通过教育 Agent 获得任务内引导，学生提交验证或解释，教师给出认可、请求说明、请求补正或标记环境问题，学生可再次提交。

这个任务验证产品工作流，不验证真实模型智能、学习效果、学生能力、外部 AI 使用或本机代码执行安全。

## 允许范围

- 一个本地、无外部网络依赖的合成演示；
- 教师、学生、任务、Agent 对话、提交、复核和补正的最小版本化数据模型；
- `ScriptedGuidanceAdapter` 或等价确定性适配器，用于模拟教育 Agent 的任务内引导；
- 最小用户界面或可复现交互演示；
- 单元、集成和合成端到端测试，以及 `artifacts/R0-AGENT-FIRST-VERTICAL-SLICE/` 下的运行证据。

## 禁止范围

- 真实模型供应商、模型 API Key、第三方模型调用或模型费用；
- 真实学生、真实身份、真实作业、个人信息或研究导出；
- 本机文件读取/写入、Shell、代码执行、依赖安装、浏览器/桌面控制或网络扫描；
- 自动评分、作弊判断、能力结论、全量日志监控、部署或 ECS 连接；
- 将确定性模拟回答描述为真实教育 Agent 效能。

## 最小领域与状态

```text
Task: DRAFT → ASSIGNED
Student work: IN_PROGRESS → SUBMITTED → REVIEW_REQUIRED / FEEDBACK_REQUIRED
Feedback: ACKNOWLEDGED | EXPLANATION_REQUESTED | REMEDIATION_REQUESTED | ENVIRONMENT_ISSUE
Remediation: FEEDBACK_REQUIRED → RESUBMITTED → CLOSED
```

每项 Agent 对话、学生提交和教师动作必须关联任务、角色、时间、版本和状态原因。`REVIEW_REQUIRED` 仅表示教师需查看；不得表示违规、作弊或能力不足。

## 验收

| ID | 条件 | 最小证据 |
| --- | --- | --- |
| AF-01 | 教师可基于固定合成模板配置任务目标、固定的允许协作方式、学生责任和提交要求。 | schema/unit test；文字字段配置扩展见 `../R0-TEACHER-TASK-AUTHORING/README.md`。 |
| AF-02 | 学生可查看任务并向确定性 Agent 请求任务内引导；适配器不会调用网络或本机工具。 | adapter unit test 与调用记录。 |
| AF-03 | 学生必须提交任务关联的验证、解释、纠错或补正之一，不能只有 Agent 文本。 | validation test。 |
| AF-04 | 系统形成最小提交：任务版本、适配器版本、学生说明、状态和事件引用。 | manifest/schema test。 |
| AF-05 | 教师可认可、请求说明、请求补正或标记环境问题；每项动作有可解释理由。 | state-machine test。 |
| AF-06 | 学生可回应说明或补正并重新提交；完整关系可回放。 | integration test。 |
| AF-07 | 任何界面/报告均不把事件解释为作弊、外部 AI 使用或能力结论。 | content/negative test。 |
| AF-08 | 使用至少四个冻结合成案例演示正常完成、请求说明、请求补正和环境问题。 | bounded demo Artifact。 |

## 停止条件

出现以下任一情况即停止扩大范围并记录：需要真实模型、外部网络、真实学生数据、身份接入、部署、本机代码执行，或需求变成自动评分/作弊判断。真实模型路线须由单独 ADR 决定后才可继续。

网络边界说明：此停止条件指本应用/Agent 要直接访问外部网络、使用浏览器工具或联网搜索的功能，不限制学生自行使用浏览器和课程网站；系统不观察或收集学生外部浏览活动。

## 实施证据

- 运行证据：`../../artifacts/R0-AGENT-FIRST-VERTICAL-SLICE/demo.json`，包含正常完成、请求说明、请求补正和环境问题四个冻结合成案例。
- 测试：`../../tests/test_agent_first_vertical_slice.py`，覆盖任务/角色状态、确定性引导、空提交拒绝、教师动作、补正与禁止推断。
- 汇总：`../../artifacts/PRODUCT-DIRECTION-CLARIFICATION-001/DECISION_AND_GATE_A_REPORT_2026-09-24.md`。
