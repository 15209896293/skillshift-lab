# R0 Foundation Spike 实施报告

## 状态

- 日期：2026-09-24。
- 总结：**PARTIAL / 不可进入下一 R0 平台纵向闭环。**
- 范围：合成 Python、本机参考 Node、受限路径、受控运行、超时停止、append-only 本地事件和本地 Manifest。
- 未实现：真实 LLM、模型密钥、网络同步、教师 Web、身份、真实学生数据、部署和真实研究。

## 已执行证据

```text
python -m py_compile execution/providers/local_restricted_process.py apps/student-studio/reference_node.py apps/student-studio/run_foundation_demo.py tests/test_foundation_spike.py
python -m unittest discover -s tests -p "test_*.py" -v
python apps/student-studio/run_foundation_demo.py
```

结果：标准库 `unittest` 的 6 项测试中 5 项通过，1 项因 Windows 当前环境没有创建符号链接权限而跳过；合成演示生成了 `submission-manifest.json`、`events.json`、合成 Workspace 中的 `result.txt` 和限制说明。

## 规格验收映射

| 条件 | 状态 | 证据 / 限制 |
| --- | --- | --- |
| FS-01 根目录绑定 | PASS | `test_rejects_workspace_escape`。 |
| FS-02 路径、绝对路径、符号链接和跨 Workspace 拒绝 | PARTIAL | 路径与绝对路径通过；根路径在规范化前的链接拒绝已有回归测试。目录符号链接实测仍被 WinError 1314 环境权限阻断，且 junction/reparse point 与 TOCTOU 未验证。 |
| FS-03 合成 Python 受控运行 | PASS | `test_runs_frozen_python_script_and_creates_manifest` 与合成演示。 |
| FS-04 任意命令、依赖、网络与超时控制 | FAIL | 接口没有一般 Shell 或依赖安装入口，超时通过；但没有操作系统级网络隔离，不能声称网络请求受限。 |
| FS-05 暂停、停止、接管与进程树 | PARTIAL | 超时后根进程停止通过；没有子进程树的可靠 Windows 级验证，暂停/接管 UI 不在此参考 Node。 |
| FS-06 append-only、重放/乱序防护 | PARTIAL | 本地事件单调序列通过；服务端同步和重放/乱序处理未实现，Manifest 诚实标为 `NOT_IMPLEMENTED`。 |
| FS-07 可复核 Manifest | PASS | Manifest 包含版本、验证结果、Artifact 哈希、事件引用和同步状态。 |
| FS-08 无真实学生/密钥/私人目录 | PASS（合成范围） | 演示仅使用合成 Workspace；未测试真实用户环境。 |

## 生成物哈希

| 文件 | SHA-256 |
| --- | --- |
| `apps/student-studio/reference_node.py` | `B0A7B25FFAA204D998D5B51C2103AE49ED53A44DDAEC7D7F5DC37435211C8900` |
| `apps/student-studio/run_foundation_demo.py` | `37B089BC7040BC6D62DCF07EFD2F8534A3339BF22201C81A086821A5777D8DBF` |
| `execution/providers/local_restricted_process.py` | `B7EBC64DE844C023CAE1B706043726741DB5E75CE666A0C35C138BA9CDF0C721` |
| `tests/test_foundation_spike.py` | `E93717AEAD69F0ED644E9EC6D4FF36DD9898F8A99D5A1A3228893BA4EBA981DC` |

## 结论与后续

这项 Spike 已验证“最小本机 Workspace 与提交包”的工程起点，但没有验证安全沙箱。下一步不能直接实现教师 Web 或真实 Agent 平台。

继续前需先决定并实现：可验证的 Windows 受限执行/网络策略、可追踪进程树终止、可创建符号链接的安全测试环境或等价验证、以及服务端事件顺序和重放防护。上述四项得到客观 PASS 后，才能创建下一份教师任务—学生协作—提交—复核—补正的工程规格。

## 后续状态校正（2026-09-24）

本报告主体记录 Foundation 首次 Spike 阶段状态。其“只有本 Spike 关闭后才可提出教师任务闭环”的建议已被较高优先级、后续接受的 Agent-first 产品决策取代：教师—学生教育 Agent Web 闭环是独立路径，明确不使用本机代码执行 Provider，可按 ADR-004 与独立规格继续；这不改变本 Spike 自身 PARTIAL，也不开放学生代码执行。

后续 Gate 1 实测细节见 `../R0-WINDOWS-ISOLATION-LAUNCHER-SPIKE/SPIKE_REPORT.md`、`APPCONTAINER_PYTHON_REPORT.md`、`COPIED_RUNNER_REPORT.md` 与 `NETWORK_DENIAL_REPORT.md`：标准 CreateProcess Job Object 样例有受限进程树终止证据；临时复制 Python Runner 有一次 AppContainer 启动 PASS；网络负测中 IPv4 UDP `sendto` 仍成功（退出码 82），故纯 AppContainer 路线不能关闭 FS-04。以上原语证据未集成到 Foundation Provider，也不关闭 FS-05。

本轮 `test_foundation_spike.py` 模块复跑：6 项、5 PASS、1 SKIP（当前 Windows 环境符号链接权限受限）；Foundation 状态仍 **PARTIAL**。Windows AppContainer 复合测试本轮未执行，不能由其他模块的回归通过推定其通过。

FS-02 另有后续静态修复：`R0-FOUNDATION-SYMLINK-GUARD-REPAIR` 让 Provider 在规范化根路径前检查原始根是否为符号链接，并用 mock 回归测试验证调用顺序。真实文件系统符号链接创建/绕越仍未验证；不改变本报告 FS-02 PARTIAL。
