# 临时专用 Runner AppContainer 验证报告

## 状态

- Task ID：`R0-WINDOWS-APPCONTAINER-COPIED-RUNNER-SPIKE`
- Gate：Gate 1
- 结果：**PASS（严格限于合成临时 Runner）。**

## 已验证事实

本次执行只在系统临时目录复制本机 Python 运行时；为每次新建、零 capability 的 AppContainer profile 创建唯一 SID，并通过受限 ACL 命令将该临时 Runner 的读取/执行权限授予该 SID。未修改 `C:\Python314`、Firewall、WFP、网络 capability、Workspace 或用户目录。

最新 `probe.json` 的 `copied_runner` 记录：

| 观测项 | 值 |
| --- | --- |
| profile 创建 / 删除 HRESULT | `0x00000000` / `0x00000000` |
| AppContainer token | `true` |
| Job 归属 | `true` |
| Python 退出码 | `0` |
| 进程退出后的 Job PID 列表 | `[]` |
| 临时目录 | 已由 `TemporaryDirectory` 在函数返回前删除 |

ACL 工具对临时副本内个别路径输出了诊断文字，但返回码为 0；运行时实际在 AppContainer 内退出码 0 完成。Artifact 不记录临时路径、SID 或 ACL 工具输出。

## 验收

| 条件 | 状态 | 证据 |
| --- | --- | --- |
| WCR-01 | PASS | 专用完整运行时仅在临时目录复制并用于本次合成命令。 |
| WCR-02 | PASS（本次 SID ACL） | 临时 ACL 命令成功返回，AppContainer 进程可读取并执行该 Runner。 |
| WCR-03 | PASS | `TokenIsAppContainer=true`、`IsProcessInJob=true`、退出码 0、Job 退出后为空。 |
| WCR-04 | PASS | profile 删除成功；函数返回前临时目录退出上下文并删除。 |

## 不可推出的结论

这不是网络隔离验证、Workspace ACL 验证、任意不可信代码沙箱、真实学生环境验证或生产 Runner 设计。系统 Python 的直接 AppContainer 启动仍返回 `0xC0000135`；只有本报告的临时副本路线通过。

Foundation Spike 的 FS-02、FS-04、FS-05、FS-06 状态不因本报告自动改变。下一项受限工作应验证专用 Runner 的零 capability 网络负测，且必须先设计受控端点与基线连通性证据。

Commit：`NONE`
