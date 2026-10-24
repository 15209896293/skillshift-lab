# 零 capability AppContainer 网络负测报告

- Task ID：`R0-WINDOWS-APPCONTAINER-NETWORK-DENIAL-SPIKE`
- Gate：Gate 1
- 结果：**FAIL。FS-04 继续为 FAIL。**

## 实测

测试仅在同一主机的短生命周期 IPv4/IPv6 回环端点运行；普通 Python 的 TCP、UDP 与 bind/listen 基线均成功。随后，零 capability AppContainer 中的临时专用 Runner 执行相同类别操作，返回退出码 `82`。

分项退出码约定为 IPv4 TCP=`81`、IPv4 UDP=`82`、IPv4 bind/listen=`83`、IPv6 TCP=`84`、IPv6 UDP=`85`、IPv6 bind/listen=`86`；全部被拒绝才返回 0。因此本次确认**IPv4 UDP `sendto` 被允许**。不能把现有 AppContainer profile 或临时 Runner 视为可验证网络边界。

## 可复核证据

| 观测项 | 值 |
| --- | --- |
| 普通 IPv4/IPv6 基线 | PASS |
| AppContainer token / Job | `true` / `true` |
| AppContainer 网络脚本退出码 | `82`（IPv4 UDP `sendto` 成功） |
| profile 创建 / 删除 HRESULT | `0x00000000` / `0x00000000` |
| 进程退出后 Job PID 列表 | `[]` |
| 网络 Artifact SHA-256 | `2CB6F68B02ADA55650CE2962E0A94FB0BA8C6291E10185A08F8B22D2824CF96B` |

## 执行

```text
python -B -m py_compile apps/student-studio/run_windows_network_denial_spike.py execution/providers/windows_isolation_spike.py
python -B apps/student-studio/run_windows_network_denial_spike.py
```

未访问公网、非回环地址、DNS 或模型服务；未变更 Firewall、WFP、路由、代理或系统 ACL。

## 限制与下一步

当前探针证明纯 AppContainer profile 路线不满足 FS-04。必须停止把它作为网络隔离方案，并在用户确认安全路线后重新评估受管 WFP 或独立执行节点；两者均不得自动部署。

Commit：`NONE`
