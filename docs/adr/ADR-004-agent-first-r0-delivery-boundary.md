# ADR-004 R0 Agent-first 交付边界

## Status

Accepted（2026-09-24）。

## Context

ADR-001 与 ADR-002 原先把学生本机受限 Python 运行列为 R0 的首条路径。Foundation Spike 已产生 PARTIAL 证据：它不能证明操作系统级网络隔离、可靠的所有子进程树停止或真实符号链接攻击防护。项目负责人已确认，首要产品目标是通用教育 Agent 的教学闭环，而不是 Agent 自动接管学生电脑执行任意代码。

若继续把本机代码执行安全证明作为首条闭环前置，会把产品验证错误地收缩为沙箱工程，并延后教师创建、学生协作、提交、复核与补正这些核心产品事实的验证。

## Decision

R0 首个可实现 vertical slice 采用 Agent-first、无本机自动执行边界：教师任务、学生平台内 Agent 协作、学生验证/解释/补正、最小提交、教师反馈与重新提交。

首个 slice 的 Agent 只通过版本化适配器处理平台内任务内容；它不获得本机文件、Shell、进程、安装依赖、任意网络或宿主机自动化工具。Gate A 可使用确定性模拟适配器验证编排与教学状态，但不得把模拟能力说成真实 LLM。

ADR-001 的混合 Web/Node 目标形态保留为长期候选；其学生 Node 和 ADR-002 的受限执行路线被降为后续可选 Evidence Adapter。任何重新引入本机读写或命令执行的 Feature，必须先建立独立规格，并以 Foundation Spike 的相关安全门槛为前置。

## Consequences

1. Foundation Spike 结果保留为 PARTIAL，且不再阻塞无本机自动执行的 Gate A。
2. 首个实现可聚焦任务、协作、提交、复核和补正的可复现状态机，而非 Windows 沙箱。
3. 真实模型供应商、数据传输和成本仍未决定；接入前需要单独 ADR 与用户决定。
4. 真实学生数据、正式课堂、部署和研究导出仍不在 Gate A 范围内。
5. 不能借由取消本机执行来放松最小数据、可解释反馈或禁止作弊推断的边界。

## Evidence

- `../product/R0_AGENT_FIRST_DELIVERY_DECISION.md`
- `../../artifacts/R0-FOUNDATION-SPIKE/SPIKE_REPORT.md`
- `../../artifacts/R0-WINDOWS-ISOLATION-LAUNCHER-SPIKE/NETWORK_DENIAL_REPORT.md`

## Related Specs / Issues

- `../../specs/R0-AGENT-FIRST-VERTICAL-SLICE/README.md`
- ADR-001、ADR-002、ADR-003

