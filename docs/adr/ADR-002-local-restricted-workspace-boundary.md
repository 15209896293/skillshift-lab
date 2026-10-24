# ADR-002 本机受限 Workspace 与受限进程边界

## Status

Proposed；作为后续本机 Code Workspace / Evidence Adapter 路线，需要 Foundation Spike 的可复现证据后才可 Accepted。它不再是 Agent-first R0 首条闭环的前置。

## Date

2026-09-24

## Context

R0 需要 Agent 在学生本机 Workspace 中读取、修改和运行 Python，同时不得访问私人目录、凭据、其他 Workspace 或任意宿主机能力。项目已确认不以 Docker 为前提，但非 Docker 受限进程不自动构成安全沙箱。

## Decision

Foundation Spike 拟使用 `LocalRestrictedProcessProvider`：每个 Workspace 绑定独立根目录；进程非管理员运行；路径二次规范化；命令、依赖、网络和资源均由 allowlist 策略控制；超时、输出、进程树和停止结果均记录。

Spike 期间只允许合成任务或负责人自有材料，默认拒绝任意依赖安装、任意网络、任意项目和真实学生数据。停止无法确认时必须呈现 `STOP_UNCONFIRMED`。

## Alternatives Considered

1. Docker/容器：当前项目已明确不作为 R0 前提。
2. 任意本机 Shell：实现快，但与隐私、安全和最小权限边界冲突。
3. 纯远程执行：可降低本机风险，但不能验证后续本机 Workspace 过程能力。

## Consequences

需要在工程前验证路径越界、符号链接、命令 allowlist、超时、子进程停止、输出限制和断网状态。Spike 失败时停止扩大范围，不以文档声明替代安全证据。

## Evidence

- `../architecture/TECHNICAL_SPEC.md`
- `../quality/QUALITY_SPEC.md`
- `../../specs/R0-FOUNDATION-SPIKE/README.md`
- `../../artifacts/R0-FOUNDATION-SPIKE/SPIKE_REPORT.md`：2026-09-24 合成 Spike 为 PARTIAL；路径/超时/Manifest 有证据，符号链接、进程树与 OS 级网络限制尚未通过。

## Related Specs / Issues

- ADR-001
- ADR-003
- ADR-004
