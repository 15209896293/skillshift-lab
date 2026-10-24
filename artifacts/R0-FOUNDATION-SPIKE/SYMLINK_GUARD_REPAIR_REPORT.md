# Foundation Spike 根路径符号链接检查修复记录

- Task ID：`R0-FOUNDATION-SYMLINK-GUARD-REPAIR`
- Gate：Gate 1
- 状态：**PARTIAL。** 静态缺口已修复；真实链接攻击验证仍被环境权限阻断。

## 修改

`LocalRestrictedProcessProvider` 现在在 `resolve()` 前检查传入 Workspace root 是否为符号链接，并在创建/绑定 Workspace 前后检查原始路径。新增回归测试通过 mock 让 `resolve()` 在错误顺序时抛出，从而验证 root 链接会先被拒绝。

## 验证

```text
python -B -m py_compile execution/providers/local_restricted_process.py tests/test_foundation_spike.py
python -B -m unittest discover -s tests -p 'test_foundation_spike.py' -v
python -B apps/student-studio/run_foundation_demo.py
```

结果：6 项中 5 PASS，1 项 SKIP（`WinError 1314`，当前令牌没有创建符号链接权限）；合成演示成功。

## 证据

| 文件 | SHA-256 |
| --- | --- |
| `execution/providers/local_restricted_process.py` | `B7EBC64DE844C023CAE1B706043726741DB5E75CE666A0C35C138BA9CDF0C721` |
| `tests/test_foundation_spike.py` | `E93717AEAD69F0ED644E9EC6D4FF36DD9898F8A99D5A1A3228893BA4EBA981DC` |
| `submission-manifest.json` | `5EC12716F74E98A3926ED56A7FF6B1BA42F2E364A776A08FDE86A23750ABCE6B` |
| `events.json` | `7E48B4D84649145F57A5C83DF2877C4AD0B8D50843574E4D89801963440B437E` |

## 仍未解决

不能把 mock 回归测试或路径代码当作实际攻击验证。目录/文件符号链接、root/Workspace 链接、junction/reparse point、跨 Workspace 与 TOCTOU 仍需在可创建链接的隔离测试环境中验证。FS-02 保持 PARTIAL；不进入 Gate 2。

Commit：`NONE`
