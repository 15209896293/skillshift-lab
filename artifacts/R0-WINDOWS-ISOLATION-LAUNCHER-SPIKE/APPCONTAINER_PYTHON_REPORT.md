# AppContainer Python 启动验证报告

## 状态

- Task ID：`R0-WINDOWS-APPCONTAINER-PYTHON-SPIKE`
- Gate：Gate 1
- 结果：**PARTIAL / 未通过 WAP-02。**

## 已实测事实

以唯一、零 capability profile 通过 `CreateProcessW` 启动 `python -I -c` 合成命令，且该进程先被创建为 suspended，再加入 Job Object。

最新 `probe.json` 记录：

| 观测项 | 值 |
| --- | --- |
| AppContainer profile 创建 / 删除 HRESULT | `0x00000000` / `0x00000000` |
| 合成进程 PID | `32400` |
| `TokenIsAppContainer` | `true` |
| `IsProcessInJob` | `true` |
| 退出码 | `3221225781`（`0xC0000135`） |
| 进程退出后的 Job PID 列表 | `[]` |

因此，本机可创建并清理零 capability profile，也可创建具有 AppContainer token 且受 Job 管理的 Python 进程；但该 Python 命令没有以退出码 0 完成。该运行器为避免意外继承输出/句柄，没有收集子进程 stderr；**不能仅凭退出码断言其精确根因。**

## 验收

| 条件 | 状态 | 结论 |
| --- | --- | --- |
| WAP-01 | PARTIAL | AppContainer token 与合成 Python 进程均有实测，但进程未成功完成。 |
| WAP-02 | FAIL | Job 归属与退出后为空通过，正常退出码 0 未满足。 |
| WAP-03 | PASS（报告语义） | 运行器返回 `FAIL`，没有将失败伪装为隔离成功；profile 已删除。 |
| WAP-04 | PASS（本次 payload） | 记录仅含 synthetic PID、状态、HRESULT 和退出码；没有用户路径、网络地址、凭据或学生数据。 |

## 执行与验证

```text
python -B -m py_compile execution/providers/windows_isolation_spike.py apps/student-studio/run_windows_isolation_spike.py tests/test_windows_isolation_spike.py
python -B -m unittest discover -s tests -p 'test_windows_isolation_spike.py' -v
python -B apps/student-studio/run_windows_isolation_spike.py
```

测试结果为 5 / 5 PASS；其中 AppContainer 测试断言的是失败状态会被明确记录，而不是把 WAP-02 标为通过。运行输出见同目录 `probe.json`。

## 停止与下一步

本规格禁止在 Python 启动失败后直接授予系统 Python、用户目录或任意 Workspace 的额外 ACL，也禁止转回普通 `subprocess`。因此本子 Spike 到此停止，不进行 ACL 或网络测试。

下一步需先形成新的、独立的“最小解释与兼容性诊断”规格，明确是否允许在完全独立测试帐户/机器上对受控 Python 运行时做只读依赖调查，或是否评估可打包的专用 Runner；该选择会影响未来受信任计算基与维护路线，不能用本次失败自动决定。

Foundation Spike 的 FS-02、FS-04、FS-05、FS-06 状态不变；不得进入 Gate 2。

## Commit

`NONE`
