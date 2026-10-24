# R0-WINDOWS-APPCONTAINER-PYTHON-SPIKE：零网络能力 Python 启动验证

## 状态

- Task ID：`R0-WINDOWS-APPCONTAINER-PYTHON-SPIKE`
- 类型：DEV_OS / 安全 Spike
- 状态：**Implemented / PARTIAL（2026-09-24）。**
- 前置证据：`R0-WINDOWS-ISOLATION-LAUNCHER-SPIKE` 的 WIL-01 至 WIL-04。

## 目标

在唯一、临时、零 capability 的 AppContainer profile 中，以 Windows `CreateProcessW` 与 `PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES` 启动 `python -I -c` 合成命令。验证进程 token 报告为 AppContainer、可被 Job Object 管理、按时退出，profile 最终被删除。

## 明确不验证

- 不配置或验证 Workspace ACL；
- 不读取、写入或上传任何 Workspace/学生文件；
- 不建立、拦截、检测或测量网络连接；
- 不声称 FS-04 已通过；
- 不使用模型、密钥、ECS、真实学生数据、Firewall、WFP、Docker、虚拟机或部署。

## 允许范围

仅可新增/修改本 Spike 的规格、`execution/providers/windows_isolation_spike.py`、运行器、测试与对应 Artifact。运行必须在 5 秒内结束；profile 创建后必须在 `finally` 删除；任一失败为 `BLOCKED` 或 `FAIL`，不得提权或改策略。

## 验收

| ID | 条件 | 最小证据 |
| --- | --- | --- |
| WAP-01 | AppContainer token 成功创建合成 Python 进程。 | `TokenIsAppContainer=true`、进程 PID、零 capability profile 生命周期。 |
| WAP-02 | 进程在 Job 中并可在有限等待内正常退出。 | `IsProcessInJob=true`、退出码 0、Job 进程列表为空。 |
| WAP-03 | 失败/超时不伪称成功，profile 仍被清理或明确报告清理失败。 | 负向单元测试与 JSON 状态。 |
| WAP-04 | 运行记录不含用户目录、真实 Workspace、网络地址、凭据或学生数据。 | 字段审阅测试。 |

若 Python 不能在此边界启动，结论是 AppContainer 兼容性 `BLOCKED/FAIL`；不得降级至普通 `subprocess`，也不得进入 ACL 或网络测试。
