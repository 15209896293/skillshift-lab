# SkillShift R0 后续开发交接手册

## 1. 本手册用途

本手册交给后续主控 Agent 使用。主控 Agent 负责持续推进 SkillShift R0，但必须通过文件、规格、证据、ADR 和可复现产物管理工作；不得把聊天记录、Agent 自述或长期运行的终端会话视为正式项目状态。

当前阶段是：**研究主线下的 R0 Foundation Spike 已开始，结果为 PARTIAL。** 这不是完整产品开发完成，也不授权真实学生试用、真实模型、部署或未验证的本机代码执行。

### 2026-09-24 产品方向更新

项目负责人已确认，R0 首条闭环先做无本机自动执行的通用教育 Agent 工作流：教师创建任务 → 学生平台内协作并提交验证/解释 → 教师复核 → 学生补正。`docs/product/R0_AGENT_FIRST_DELIVERY_DECISION.md` 与 ADR-004 是这项更新的权威记录。

因此，本手册中“必须先关闭 Foundation Spike 才能开发教师—学生闭环”的旧顺序只适用于未来本机 Code Workspace / 自动代码执行路线，不适用于首条 Agent-first 闭环。Foundation Spike 的 PARTIAL 结论和所有安全限制仍然有效，不能被描述为已解决。

## 2. 必须先读的顺序

1. `AGENTS.md`
2. `README.md`
3. `docs/README.md`
4. `docs/PROJECT_FILE_GOVERNANCE.md`
5. `docs/product/R0_AGENT_FIRST_DELIVERY_DECISION.md`
6. `docs/product/R0_PRODUCT_REPOSITIONING_DECISION.md`
7. `docs/product/R0_RESEARCH_TASK_EVIDENCE_CONTRACT.md`
8. `docs/product/REQUIREMENTS_SPEC.md`
9. `docs/architecture/TECHNICAL_SPEC.md`
10. `docs/quality/QUALITY_SPEC.md`
11. `docs/adr/ADR-004-agent-first-r0-delivery-boundary.md` 与 ADR-001 至 ADR-003；ADR-005 为已否决的 OpenAI 历史记录，当前国内模型研究见 `docs/product/DOMESTIC_EDUCATION_AGENT_MODEL_ROUTE_RESEARCH.md`
12. `specs/R0-AGENT-FIRST-VERTICAL-SLICE/README.md`
13. `specs/R0-FOUNDATION-SPIKE/README.md` 与 `artifacts/R0-FOUNDATION-SPIKE/SPIKE_REPORT.md`
14. `docs/CURRENT_STATE.md`

若有冲突，使用 `AGENTS.md` 的来源优先级；不得按便利性静默选择旧文档。

## 3. 产品事实与边界

SkillShift Lab 的核心是研究 Agent 如何改变职业教育知识、基础能力、任务结构和人机协同。SkillShift Studio 是产品化研究基础设施：提供真实任务、允许 AI 协作、最小必要过程证据和教师干预入口。

R0 首先验证：

- A：教师/导师能否低负担完成“创建任务—复核—补正”；
- B：学生在允许 Agent 时能否完成与任务相关的验证、解释、纠错、接管或补正。

R0 不验证或不得声称：外部 AI 被阻止、学生没有使用其他工具、学生真实能力已被自动证明、作弊结论、AI 替代率、学习效果、学校采购或正式课堂可行性。

目标形态是：

```text
教师/导师 Web 端
        +
学生桌面 Studio / Agent Node
        +
平台服务端
```

学生桌面 Node 只处理绑定 Workspace 内的 Agent、文件和受限运行；不得监控全桌面、私人目录、浏览历史、手机或其他应用。它是后续可选 Evidence Adapter，不是当前首条闭环。Python 不是产品永久边界。

## 4. 已有实现与证据

已实现的只是合成本机参考 Node，不是可供学生使用的产品：

| 路径 | 内容 |
| --- | --- |
| `execution/providers/local_restricted_process.py` | 路径限制、冻结 Python 脚本运行、超时、输出截断、根进程停止。 |
| `apps/student-studio/reference_node.py` | 本地 append-only 事件与最小提交 Manifest。 |
| `apps/student-studio/run_foundation_demo.py` | 可复现合成演示。 |
| `tests/test_foundation_spike.py` | 标准库 `unittest` 测试。 |
| `artifacts/R0-FOUNDATION-SPIKE/` | Manifest、事件、合成 Artifact、限制说明与 Spike 报告。 |

已验证：根目录/绝对路径拒绝、合成 Python 运行、超时根进程停止、事件序列、Artifact 哈希和本地 Manifest。

未通过或未充分验证：

1. 没有操作系统级网络隔离，不能称安全沙箱；
2. 没有可靠的 Windows 子进程树终止验证；
3. 当前环境无符号链接创建权限，实际攻击路径未验证；
4. 没有服务端事件同步、重放防护或乱序处理；
5. 没有真实 LLM、模型密钥、教师 Web、账号、部署或真实学生数据。

因此 `artifacts/R0-FOUNDATION-SPIKE/SPIKE_REPORT.md` 的结论是 PARTIAL。**未关闭这些问题前，禁止把该 Provider 用于外来/学生项目或将其描述为安全沙箱。** 无本机自动执行的 Agent-first 纵向闭环依 ADR-004 另行推进。

## 5. ECS 状态与使用边界

已有一台 Ubuntu 24.04 ECS，2 vCPU / 3.5 GiB / 40 GB。它已通过 SSH 只读核验：

- `skillshift` 普通用户的 SSH 公钥登录和 sudo 可用；
- root SSH 和密码 SSH 已禁用；
- UFW 默认拒绝入站，仅放行 22；fail2ban sshd 已启用；
- 无业务端口、产品部署、模型密钥、Docker 或学生代码。

服务器只可作为后续的平台控制面候选：API、教师 Web、模型网关、任务元数据和提交包元数据。它**不得**直接运行任意学生代码。

服务器连接信息和私钥路径属于敏感运行信息：不要写入 Git、Markdown、日志、截图或 Prompt；不要请求用户在聊天中发送密码、私钥、AccessKey 或模型密钥。

## 6. 下一阶段的正确顺序

### Gate 0：工作区与证据审计

- 读取所有来源文件，执行 `git status`；保留现有未提交文件和 P0-A 历史材料。
- 检查 Foundation Spike 的 Manifest、事件、报告和测试是否仍匹配代码。
- 不自动提交、推送、部署、删除、重置或清理。

### Gate 1：受限执行安全路线（后续可选）

在实现更多产品前，主控 Agent 可并行委派只读调查与小型、隔离 Spike，回答：

- Windows 本机 Node 能否用 Job Object、AppContainer、受限令牌、Windows Firewall/WFP 或等价方式实现可验证的网络/进程限制？
- 若不能，受管远程执行是否应另建隔离节点，而不是使用现有平台 ECS？
- 如何在可创建符号链接的安全测试环境中验证路径策略？

任何方案在没有证据前必须标 Proposed。不得为“继续开发”而把不安全的 Python 子进程当作安全沙箱。

### Gate 2：关闭 Foundation Spike（仅本机 Code Workspace 路线）

只有 FS-01 至 FS-08 都有客观证据，才可将 Foundation Spike 标为 Verified。此前不能让 Agent 运行外来/学生项目、开放本机工具或把 Provider 说成安全沙箱。

### Gate A：Agent-first 单一纵向闭环

依据 `specs/R0-AGENT-FIRST-VERTICAL-SLICE/README.md` 实施：合成任务 → 学生平台内协作 → 最小提交包 → 教师复核 → 学生补正。该阶段不做真实模型、完整 LMS、正式成绩、研究导出、多任务扩张或本机代码执行。

### Gate 4：教师流程验证与非计分试用

先以合成案例和少量教师验证摘要与复核动作；随后才讨论明确告知的非计分自愿使用。任何研究数据使用另需独立授权。

## 7. 主控 Agent 的多 Agent 协作规则

主控 Agent 可以委派，但自己必须保持唯一的架构/文档集成者。

| 角色 | 可委派的边界 | 禁止事项 |
| --- | --- | --- |
| 安全研究 Agent | Windows 本机隔离方案、威胁模型、官方资料与可验证实验设计。 | 不直接改主架构或声称安全。 |
| Node Spike Agent | 在独立工作树或隔离目录实现一个明确的安全 Spike。 | 不接真实学生、模型、云密钥或无关平台功能。 |
| 产品/教学 Agent | 审阅任务模板、人类责任、教师工作量和补正流程。 | 不把日志解释为能力或作弊结论。 |
| QA Agent | 审计规格、测试、负向路径、Artifact 和报告。 | 不擅自修复或通过跳过测试宣称成功。 |
| 服务端规划 Agent | 仅规划 ECS 控制面、部署前安全与数据边界。 | 不把现有 ECS 当作任意代码执行器。 |

协作要求：

1. 每项委派必须有 Task ID、目标、允许范围、禁止范围、验收证据和停止条件。
2. 多 Agent 不得同时改同一份权威文档；主控 Agent 最后单独整合。
3. 涉及多文件代码或高风险变更时，优先使用独立 Worktree；当前工作区有未提交内容，先审计再决定。
4. 运行命令必须有边界和超时；禁止无限循环、无期限开发服务器、长期占用终端或用睡眠代替状态检查。
5. 长期推进意味着跨轮次保持任务状态，不意味着无证据地不断扩展范围。
6. 每一阶段结束必须写入文件化报告；若出现阻断，记录证据、停止扩大范围并向用户汇报。

## 8. 每次汇报必须包含

- Task ID；
- 当前 Gate；
- 文件变化及原因；
- 已执行命令和结果；
- 验收项 PASS / PARTIAL / FAIL；
- Artifact 路径、哈希或其他可复核证据；
- 已知限制与新风险；
- 下一步及是否需要用户决定；
- Git diff 摘要；
- Commit：`NONE`，除非用户明确要求提交。

## 9. 绝对禁止

- 自动提交、推送、部署、删除、`git reset --hard`、`git clean`；
- 使用真实学生数据、学生隐私数据、模型密钥或研究导出；
- 将运行日志、粘贴、相似度或过程缺失自动解释为作弊或能力；
- 让现有 ECS 执行任意学生代码；
- 让 Node 访问全桌面、私人目录、凭据、其他 Workspace 或无关应用；
- 因为“主控 Agent 长时间运行”而跳过用户决策、规格、测试或安全门槛。
