# SkillShift Studio R0 质量规范

## 状态与效力

- 状态：**Active**（2026-09-24）；适用于 Agent-first R0 合成闭环。
- 上游：`../product/R0_AGENT_FIRST_DELIVERY_DECISION.md`、`../product/REQUIREMENTS_SPEC.md`、`../architecture/TECHNICAL_SPEC.md`、ADR-004。
- 不代表：测试通过即学习效果、真实学生安全、真实模型质量或正式课堂可行性。

## 1. 通用质量要求

- 每项功能映射到需求 ID、验收条件和可复核证据；聊天记录或截图不能是唯一证据。
- 任务、适配器、提交、复核动作和事件必须有稳定 ID 与版本。
- 事件只能追加；纠正以新事件或明确状态迁移表达。
- 教师动作必须带理由；任何理由均不得自动定性作弊、外部 AI 使用、能力或努力程度。
- 失败、冲突、缺失、适配器不可用和环境问题必须可见，不能伪装成学生过程不足。

## 2. Gate A 隐私与安全

- 仅处理冻结合成任务与模拟身份；不处理真实学生数据、凭据、模型 API Key 或研究导出。
- 默认 Agent 适配器不得调用网络、文件系统、Shell、浏览器自动化、子进程或外部服务。
- 不采集全桌面、私人目录、键盘记录、浏览历史、手机或其他应用活动。
- 提交包只含任务允许的学生响应、版本、状态、事件引用和教师反馈；不整体上传本机目录。
- ADR-005 的 OpenAI 网关记录已被否决并仅作历史保留；任何国内或其他真实模型调用、身份、持久数据、部署或第三方服务接入仍需受控运行时配置与对应验证。
- ADR-006 的 Gate B 本地契约必须拒绝任意 provider、endpoint、工具或联网搜索配置；模型不可用必须可见地失败或使用有记录的确定性降级，不能静默改用另一供应商。
- 模型档案、事件、Manifest、错误和 Artifact 不得出现明文 Key、secret 或凭据引用；学生不能改变模型、费用、工具或回退策略。

## 3. 分层测试

工作区合成 API 的 strict DTO 测试用 `jsonschema` 校验 `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json`；这是测试依赖，不是产品运行时依赖。首次运行该 schema 测试前执行 `python -m pip install -r requirements-test.txt`，再使用 `python -m unittest discover -s tests -v`。Schema 的 `maxLength` 以 Unicode 字符计数；API 的正式文本上限仍必须由实现按 UTF-8 字节单独检查和测试。

| 层级 | Gate A 最小验证 |
| --- | --- |
| Static | 格式、依赖、schema 与禁止的外部调用检查。 |
| Unit | 任务校验、角色权限、状态迁移、学生责任校验、适配器确定性和事件构造。 |
| Integration | 创建任务、Agent 引导、提交、教师动作、补正和重提。 |
| E2E | 正常完成、请求说明、请求补正、环境问题四个冻结合成案例。 |
| Negative | 空学生响应、越权教师动作、伪造状态、适配器外部调用和禁止推断文本。 |
| Recovery | 适配器失败、重复提交、乱序事件和未完成补正的可见状态。 |

## 4. 后续本机执行的额外门槛

一旦 Feature 引入本机 Workspace、文件访问、命令运行、子进程、依赖安装或 Agent 网络工具，必须额外适用 ADR-002、Foundation Spike 与独立安全规格。届时路径越界、符号链接、跨 Workspace、停止/进程树、网络策略和凭据泄露必须有真实负向证据。

Gate A 不以未通过的 Foundation Spike 为安全承诺，也不调用其 Provider。

## 5. Verified 的判定

一个 Gate A 功能只有在需求可追溯、相关测试通过、至少一条失败路径经验证、事件/版本/Artifact 可定位、限制已记录且无未解释高风险回归时，才可称 `Verified`。无真实模型和真实学生证据时，不得扩展该称谓。
