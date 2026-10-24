# ADR-003 最小提交包、Artifact 同步与数据边界

## Status

Proposed；真实学生试用前必须确认。

## Date

2026-09-24

## Context

Workspace 位于学生本机，但教师复核需要可定位的结果、验证依据和有限过程事实。全量上传本机目录会扩大隐私和安全风险；仅保存本机路径又无法让教师长期复核。

## Decision

每次提交拟生成最小 Manifest：任务/模板/验证器版本、Node/运行环境/Agent/模型引用、验证结果、事件引用、允许 Artifact 的相对路径/哈希/大小、学生说明和同步状态。原始 Workspace 默认不整体上传；Artifact 内容仅在任务契约允许且完成权限/敏感信息检查后上传。

教师只可查看已同步、被任务允许且与其角色相关的提交内容。同步失败、事件冲突和缺失必须明确显示；本机路径不能被视为远程可复核内容。运营数据与研究数据分离。

## Alternatives Considered

1. 整个 Workspace 云同步：复核方便，但超出最小必要数据原则。
2. 仅保留本机路径：隐私较少，但教师无法复核且设备丢失即证据断裂。
3. 全量屏幕/桌面记录：不符合过程治理边界，也不能证明学习。

## Consequences

仍需由项目负责人和后续校内治理确认：Artifact 允许类型、加密、服务端存储、保留期限、学生退出/删除、导出审批和灾难恢复。未确认前不得处理真实学生数据或做研究导出。

## Evidence

- `../product/REQUIREMENTS_SPEC.md`
- `../product/R0_RESEARCH_TASK_EVIDENCE_CONTRACT.md`
- `../architecture/TECHNICAL_SPEC.md`
- `../quality/QUALITY_SPEC.md`

## Related Specs / Issues

- `../../specs/R0-FOUNDATION-SPIKE/README.md`
- ADR-001、ADR-002
