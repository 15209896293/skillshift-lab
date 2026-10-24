# R0 Windows 隔离启动器可行性 Spike 报告

## 状态

- Task ID：`R0-WINDOWS-ISOLATION-LAUNCHER-SPIKE`
- Gate：Gate 1
- 日期：2026-09-24
- 结果：**PARTIAL。** 本报告增加 Windows Job Object 与 AppContainer profile 生命周期的运行证据；它没有关闭 Foundation Spike 的 FS-02、FS-04、FS-05 或 FS-06。

## 范围

本次只运行短生命周期、临时目录中的合成 Python 父/子进程；创建并立即删除一个唯一、零 capability 的 AppContainer profile。没有启动 AppContainer 内的 Python、配置 Workspace ACL、尝试网络、修改 WFP/防火墙、提权、访问 ECS、处理学生数据或模型密钥。

## 实际命令与结果

```text
python -B -m py_compile execution/providers/windows_isolation_spike.py apps/student-studio/run_windows_isolation_spike.py tests/test_windows_isolation_spike.py
python -B -m unittest discover -s tests -p 'test_windows_isolation_spike.py' -v
python -B apps/student-studio/run_windows_isolation_spike.py
python -B -m unittest discover -s tests -p 'test_foundation_spike.py' -v
```

- Windows Spike：4 / 4 PASS。
- 既有 Foundation Spike：4 PASS / 1 SKIP；符号链接测试仍被 `WinError 1314` 阻断。
- 初次按模块名运行 `python -m unittest tests.test_windows_isolation_spike -v` 因 `tests/` 未作为 Python package 而失败；未把该结果计为通过，随后以上述项目既有 discover 方式复跑通过。

## 验收映射

| 条件 | 状态 | 客观证据 | 不能推出的结论 |
| --- | --- | --- | --- |
| WIL-01 | PASS（限定标准 CreateProcess 子进程） | `probe.json` 记录父 PID `26604`、子 PID `25996` 均处于 Job；终止后 `active_pids_after_terminate=[]`，两者均已退出。 | 任意进程创建路径、breakaway 行为或生产进程树隔离已经安全。 |
| WIL-02 | PASS（原语失败不伪报成功） | `test_invalid_process_handle_is_not_reported_as_job_assignment_success` 通过。 | Node 已具备暂停、接管、停止状态机或 `STOP_UNCONFIRMED`。 |
| WIL-03 | PASS（profile 生命周期） | `probe.json` 的 create/delete HRESULT 均为 `0x00000000`。 | AppContainer 内的 Python 可启动、Workspace ACL 正确或网络已隔离。 |
| WIL-04 | PASS（本次生成 payload） | payload 测试确认不含用户主目录或 `\\Users\\` 字符串；只记录 synthetic PID、状态和 HRESULT。 | 真实学生环境已经完成数据审计。 |

`probe.json` 中的 PID 只是本次短生命周期合成进程的诊断事实，不代表用户、学生或设备身份。

## Foundation Spike 状态

- FS-02：**PARTIAL**。符号链接真实攻击验证、根链接/junction/reparse point 与 TOCTOU 仍无证据。
- FS-04：**FAIL**。本次没有启动 AppContainer 进程或执行受控网络负测，仍无操作系统级网络隔离证据。
- FS-05：**PARTIAL**。Job Object 原语已有受限实测，但现有 `LocalRestrictedProcessProvider` 未使用它，且 Node 的暂停、接管和 `STOP_UNCONFIRMED` 未实现。
- FS-06：**PARTIAL**。本地内存事件没有服务端同步、重放、乱序或缺失处理。

因此不得进入 Gate 2、教师 Web、真实模型、真实学生数据、网络同步或部署。

## 产品路线适用范围校正（2026-09-24）

上句是本机代码执行路线的早期 Gate 1 停止意见，不阻止 ADR-004 单独授权的 Agent-first 教师/学生网页闭环。该闭环不使用本 Spike 的代码执行 Provider，已由独立规格实现合成验证。此校正不关闭 Foundation FS-02/04/05/06，不授权真实模型、真实学生数据、网络策略修改或部署。学生自行访问互联网/课程网站不在本 Spike 的限制范围内；网络负测只针对隔离进程。

## 哈希

| 文件 | SHA-256 |
| --- | --- |
| `execution/providers/windows_isolation_spike.py` | `1DC9075180057DEAEB868ED8FBB7EEF391C0D5F78D8D9BE6375A181E2F30D089` |
| `apps/student-studio/run_windows_isolation_spike.py` | `CC35FEB3D3895EE8916FBAA7B380AF48AE3DCFFB844FCBF3961E07C74A4E3B1C` |
| `tests/test_windows_isolation_spike.py` | `50292C6434AD82F4A125D0133515FF2A963B5916455E559785D9C18F785BD7E6` |
| `artifacts/R0-WINDOWS-ISOLATION-LAUNCHER-SPIKE/probe.json` | `98B6BE9C64006ED907C59FF443BB2D73C896DC23E3D221BD3A5A9831C65ED938` |

## 已知限制、风险与下一步

AppContainer profile 创建成功不等于用户对 profile 外的路径有 ACL；Job Object 默认子进程语义不覆盖所有非标准创建方式；网络隔离不能从未连接网络推断。下一步只能提出独立的 Phase B 规格：启动 AppContainer 内合成 Python、授予最小临时 Workspace ACL，并在受控端点完成基线与隔离网络负测。任何 profile/ACL 失败均必须 fail-closed 并记录，不得转回普通 `subprocess`。

## Git

- 本 Task 新增独立 Spike 规格、原语探针、运行器、测试和证据报告；未修改既有 Provider 或权威 R0 文档。
- `git diff --check` 通过；工作区原有已跟踪和未跟踪改动未触碰。
- Commit：`NONE`
