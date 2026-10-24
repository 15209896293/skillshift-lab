# R0-WINDOWS-APPCONTAINER-NETWORK-DENIAL-SPIKE：零 capability 网络负测

## 状态

- Task ID：`R0-WINDOWS-APPCONTAINER-NETWORK-DENIAL-SPIKE`
- 类型：DEV_OS / 安全 Spike
- 状态：**Implemented / FAIL（2026-09-24）。**
- 前置：临时专用 Runner 可在零 capability AppContainer 内运行。

## 目标

在同一主机、同一短生命周期测试中先证明普通 Python 对本地受控回环端点的 IPv4/IPv6 TCP/UDP 与 bind/listen 基线能力，再证明零 capability AppContainer 中的同一合成 Runner 无法完成这些网络动作。

## 禁止范围

- 公网、局域网非回环地址、DNS、模型/API、学生数据；
- Firewall/WFP、路由、代理、Hosts、服务安装或持久端口；
- 系统 Python 与系统 ACL 修改；
- 将单次 timeout、基线失败或未支持 IPv6 解释为网络隔离通过。

## 验收

| ID | 条件 | 最小证据 |
| --- | --- | --- |
| WN-01 | 普通 Runner 对 TCP/UDP IPv4/IPv6 和 bind/listen 的基线操作成功。 | 每项本地回环端点的成功记录。 |
| WN-02 | 零 capability AppContainer 的对应操作均被拒绝。 | 同一运行中 token、Job、各操作拒绝结果。 |
| WN-03 | profile、临时 Runner、测试端点均在 finally 关闭/删除。 | 结构化清理结果，无持久端口。 |
| WN-04 | 不含绝对路径、SID、网络以外地址、凭据或学生数据。 | Artifact 字段审阅。 |

IPv6 基线不可用、任何 AppContainer 操作成功、清理失败或观测不完整均为 PARTIAL/FAIL；不得关闭 FS-04。
