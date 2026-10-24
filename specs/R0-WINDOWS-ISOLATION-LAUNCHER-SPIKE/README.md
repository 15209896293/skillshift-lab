# R0-WINDOWS-ISOLATION-LAUNCHER-SPIKE：Windows 隔离启动器可行性验证

## 状态与授权

- Task ID：`R0-WINDOWS-ISOLATION-LAUNCHER-SPIKE`
- 类型：DEV_OS / 安全 Spike
- 状态：**Implemented / PARTIAL（2026-09-24）；不是 Accepted 架构决策。**
- 上游：`docs/HANDOFF_R0_CONTINUATION_2026-09-24.md`、ADR-002、`artifacts/GATE-1-SECURITY-ROUTE-RESEARCH/GATE_1_SECURITY_ROUTE_RESEARCH_2026-09-24.md`。

本 Spike 只处理项目负责人授权的合成脚本。它不把 Windows API 可用性、单一测试通过或 AppContainer profile 创建成功表述为安全沙箱、真实学生可用性或 Foundation Spike Verified。

## 目标

以可停止、可清理、可复核的方式验证两个 Windows 原语的**最低可行性**：

1. Job Object 是否能把一个已进入 Job 的合成父进程及其标准 `CreateProcess` 子进程作为同一组终止；
2. 当前用户能否创建并删除零 capability 的 AppContainer profile。

本阶段不尝试运行 AppContainer 内的 Python、不配置 Workspace ACL、不修改 Windows Firewall/WFP、不建立网络连接，也不修改现有 `LocalRestrictedProcessProvider`。

## 允许范围

- 新增 `execution/providers/windows_isolation_spike.py`；
- 新增 `apps/student-studio/run_windows_isolation_spike.py`；
- 新增 `tests/test_windows_isolation_spike.py`；
- 新增 `artifacts/R0-WINDOWS-ISOLATION-LAUNCHER-SPIKE/` 下的运行证据与本报告；
- 仅在系统临时目录运行短生命周期合成父子 Python 进程；若 profile 成功创建，必须在同一命令的 `finally` 中删除。

当前 R0 的规格、ADR、现有 Provider、教师/服务端/模型源代码和 ECS 均不在此任务修改范围。

由于目前 R0 规格、代码和 Artifact 是未提交工作区内容，基于 `HEAD` 建立 Worktree 会丢失本任务必需的当前输入；未经授权自动复制或提交这些内容不合适。本 Spike 因此只在当前工作区新增独立文件，且不触碰已有未提交文件。

## 禁止范围

- 真实学生或隐私数据、模型、API Key、真实 Artifact、外部服务或部署；
- Docker、虚拟机、ECS、远程执行节点；
- 防火墙/WFP/Developer Mode/安全策略/用户权限变更；
- 任何公网或局域网连接测试；
- 自动提交、推送、删除、重置、清理用户文件；
- 将创建 profile、Job Object 或进程终止的成功宣称为 FS-02/FS-04/FS-05 已关闭。

## 验收与停止条件

| ID | 条件 | 最小证据 | 成功后仍不可宣称 |
| --- | --- | --- | --- |
| WIL-01 | 合成父进程进入 Job 后，其标准子进程可被同一 Job 终止。 | 父/子 PID、`IsProcessInJob`、终止后 PID/Job 枚举记录。 | 任意 Windows 子进程创建路径或生产级进程树安全。 |
| WIL-02 | Job API 错误、观察失败或超时不被转换为成功。 | 单元负向测试与明确异常/FAIL 状态。 | `STOP_UNCONFIRMED` 已整合进 Node。 |
| WIL-03 | 当前用户的零 capability AppContainer profile 创建/删除结果可复核。 | 命名、HRESULT 与删除结果；成功则无遗留 profile。 | AppContainer Python 可运行、网络已隔离或 Workspace ACL 已正确配置。 |
| WIL-04 | 运行记录不含学生数据、密钥、私人目录或网络数据。 | 生成 JSON 的字段审阅与测试。 | 真实用户环境已审计。 |

任何 API 不可用、profile 创建/删除失败、合成子进程无法确认终止、或测试试图超出临时目录时，立即记录 `BLOCKED` 或 `FAIL` 并停止扩大范围。不得提权、修改策略或跳过失败。

## 后续门槛

只有 WIL-01 至 WIL-04 有对应证据，才可提出下一份独立规格：AppContainer 内合成 Python 启动、AppContainer SID 的最小 Workspace ACL、零网络 capability 的受控网络负测。该后续规格仍不关闭 FS-04，直到网络负测和基线连通性都可复核。
