# ADR-001 教师 Web、学生 Node 与平台服务端职责边界

## Status

Accepted（产品形态）；桌面技术、离线策略和设备绑定仍为 Proposed。

## Date

2026-09-24

## Context

纯 Web 无法可靠承载学生本机文件、Python 运行环境、Agent 停止/接管与过程事件；将教师复核、任务管理和本机执行放进同一客户端也会增加安装与权限成本。SkillShift 需要提供本机 Agent 能力，但不应成为全桌面监控或全功能 IDE。

## Decision

R0 采用混合形态：教师/导师使用 Web 端创建任务、复核和反馈；学生使用桌面 Studio / Agent Node 处理绑定 Workspace、受限 Python 运行、Agent 控制与本机事件；平台服务端处理身份、任务、提交、最小事件、模型网关和 Artifact 元数据。

Node 只控制绑定 Workspace 和平台内 Agent 行为。浏览器不直接执行本机命令；Node 不保存模型 API Key；平台不扫描全桌面或宣称观察外部 AI。

## Alternatives Considered

1. 纯 Web：适合任务管理，但不能可靠获得本机 Workspace/终端/进程控制。
2. 单一重型桌面应用：可获得本机能力，但会把教师工作流、安装和运维负担不必要地集中。
3. 直接接入 PyCharm/虚拟机：只适合作为后续部分可观察的 Evidence Adapter，不能替代首个受控 Workspace。

## Consequences

需要定义 Node 注册、更新、离线恢复、设备关系和最小 Artifact 同步；这些成本是获取真实本机协作过程的代价。R0 不承诺完整 IDE 替代、所有设备兼容或对外部 AI 的控制。

## Evidence

- `../product/R0_PRODUCT_REPOSITIONING_DECISION.md`
- `../product/REQUIREMENTS_SPEC.md`
- `../product/R0_RESEARCH_TASK_EVIDENCE_CONTRACT.md`

## Related Specs / Issues

- `../../specs/R0-FOUNDATION-SPIKE/README.md`
- ADR-002、ADR-003

## 2026-09-24 Delivery-Scope Update

ADR-004 已确认首条 R0 交付不依赖学生 Node 或本机 Python 运行：它先实现平台内教育 Agent、任务、提交、复核和补正。本文的混合 Web/Node 形态仍是后续候选；任何 Node 本机执行能力重新进入范围时，继续适用本 ADR、ADR-002 和 Foundation Spike 的相关门槛。
