# Gate 1 WFP 受管验证前置条件审计

- Task ID：`G1-WFP-READINESS-001`
- Gate：Gate 1
- 状态：**BLOCKED（仅 WFP 实施子路线）。**

## 只读事实

- 当前 token 为 Medium Mandatory Level；`BUILTIN\Administrators` 显示为 deny-only，不是提升后的管理员 token。
- Base Filtering Engine（BFE）与 Windows Defender Firewall（MpsSvc）均为 Running / Automatic。
- 三个 Firewall profile 都启用，但默认入站/出站动作显示 NotConfigured；不能据此推断实际有效策略或安全隔离。
- AppContainer 网络负测已经证明 IPv4 UDP `sendto` 被允许；纯 AppContainer route 不满足 FS-04。

## 结论

当前会话不应尝试创建、修改或测试 WFP/Firewall 规则。WFP 动态会话验证需要受管、提升后的专用测试帐户或测试设备，以及用户对该系统级安全路线的明确选择。现有 ECS 仍不得执行学生代码。

## 未执行事项

没有创建规则、调用 `netsh`、更改 profile、启动服务、提升权限、连接 ECS 或访问学生/模型数据。

## 下一步决策

1. 授权专用受管测试环境中的临时 WFP 动态会话验证；或
2. 放弃本机网络执行路线，另行规划独立受管执行节点（不使用现有 ECS）。

Commit：`NONE`
