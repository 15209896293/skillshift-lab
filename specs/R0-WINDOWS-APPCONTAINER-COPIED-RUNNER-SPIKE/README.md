# R0-WINDOWS-APPCONTAINER-COPIED-RUNNER-SPIKE：临时专用 Runner 验证

## 状态

- Task ID：`R0-WINDOWS-APPCONTAINER-COPIED-RUNNER-SPIKE`
- 类型：DEV_OS / 安全 Spike
- 状态：**Implemented / PASS（2026-09-24）；仅限合成临时 Runner。**
- 前置事实：系统 Python 在零 capability AppContainer token 下退出 `0xC0000135`；不得为修复该现象修改系统 Python ACL。

## 目标

只在 `TemporaryDirectory` 内复制运行合成 `python -I -c` 所需的专用运行时，向本次唯一 AppContainer SID 授予该临时副本的只读/执行 ACL，验证 profile、ACL、Job 与 Python 生命周期均可复核，随后删除 profile 和临时目录。

## 严格边界

- 不修改 `C:\Python314` 或其他系统/用户目录 ACL；
- 不授予写入、网络 capability、Firewall/WFP 规则、注册表、模型、真实 Workspace 或学生数据访问；
- 不将临时目录路径、ACL 命令输出、用户路径或 SID 写入 Artifact；
- 不将成功解释为 FS-04 网络隔离、任意代码安全或真实 Workspace 可用。

## 验收

| ID | 条件 | 最小证据 |
| --- | --- | --- |
| WCR-01 | 临时专用 Runner 与运行所需依赖均只在临时目录准备。 | 文件清单与哈希仅保存在运行内存；Artifact 不记录本机绝对路径。 |
| WCR-02 | 仅本次 AppContainer SID 获得临时目录读取/执行权，且命令超时/失败会被记录。 | 受控 ACL 命令退出码和 profile 生命周期。 |
| WCR-03 | AppContainer Python token、Job 和退出码 0 同时成立。 | token/Job/退出码/空 Job 列表。 |
| WCR-04 | `finally` 删除 profile 和整个临时目录；清理失败即 FAIL。 | 结构化清理状态。 |

任何 ACL 命令失败、临时路径越界、Runner 无法在 AppContainer 内完成或清理不完整，都必须为 FAIL/BLOCKED；不得改动系统 ACL 或进入网络/Workspace 测试。
