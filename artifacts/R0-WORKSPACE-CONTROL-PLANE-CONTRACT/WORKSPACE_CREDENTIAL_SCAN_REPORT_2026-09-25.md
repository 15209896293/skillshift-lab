# R0 Workspace 凭据指示器扫描报告

## 状态

- Task ID：`R0-WORKSPACE-CREDENTIAL-SCAN-001`
- 子项 Gate：本机合成 allowlist 与工作区文本静态扫描，**PASS（范围受限）**。
- 总体 R0 Workspace Gate：仍为 **PARTIAL**；本扫描不改变 HTTP/浏览器 QA、安全隔离或生产 Gate 状态。
- 范围：只读扫描 SkillShift 当前工作区文本；未读取真实学生/教师资料、真实凭据或外部系统。

## 执行方式

运行命令：

```powershell
& '.\artifacts\R0-WORKSPACE-CONTROL-PLANE-CONTRACT\scan_workspace_text_credentials.ps1' -Root 'F:\比赛\skillshift'
```

扫描器遍历项目文本文件，纳入 `.py`、JavaScript/TypeScript、JSON、Markdown、YAML、TOML、INI、文本/CSV、HTML/CSS、Shell/PowerShell、XML、ENV 和 properties 扩展名；每个文件上限 5 MiB。跳过 `.git`、依赖、缓存、构建目录及重解析点；不输出命中行内容或凭据值。检测模式包括常见私钥头、AWS/GitHub/GitLab/Slack/Google/OpenAI token 形态和长值凭据赋值。常见 `example`、`dummy`、`placeholder` 等明确占位值会从通用赋值规则排除。

未发现 `gitleaks`、`trufflehog` 或 `detect-secrets` 可执行程序，因此本次使用存档于本目录的 PowerShell 自定义指示器扫描器；没有联网安装工具。

## 结果

| 指标 | 结果 |
| --- | ---: |
| 文本文件扫描 | 236 |
| 二进制/NUL 跳过 | 0 |
| 超过 5 MiB 跳过 | 0 |
| 读取错误 | 0 |
| 模式命中 | 7 |
| 凭据值输出 | 0 |

7 条命中均在既有本机安全契约测试和说明中，逐项人工分类为明显合成的假凭据测试向量：

| 文件 | 行 | 命中类型 | 分类 |
| --- | ---: | --- | --- |
| `apps/agent-first/run_safety_contract_evidence.py` | 52 | OpenAI token 形态 | `FAKE_PROVIDER_KEY` 合成拒绝测试值 |
| `apps/agent-first/run_safety_contract_evidence.py` | 54 | 通用凭据赋值形态 | `FAKE_PASSWORD_LINE` 合成测试值 |
| `apps/agent-first/run_safety_contract_evidence.py` | 55 | 私钥头形态 | 标为 `FAKE_PEM_BLOCK` 的合成示例 |
| `specs/R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT/README.md` | 26 | 私钥头形态 | 文档内明确标为假凭据的示例 |
| `tests/test_local_safety_contract.py` | 39 | OpenAI token 形态 | `FAKE_PROVIDER_KEY` 合成拒绝测试值 |
| `tests/test_local_safety_contract.py` | 41 | 通用凭据赋值形态 | `FAKE_PASSWORD_LINE` 合成测试值 |
| `tests/test_local_safety_contract.py` | 42 | 私钥头形态 | 标为 `FAKE_PEM_BLOCK` 的合成示例 |

R0 allowlist 的 `main.py`、`orders.csv`、`README.md`，学生页嵌入样例、Workspace API、共享客户端及教师/学生 UI 均没有匹配项。以上结论来自此次模式扫描和这 7 条命中的脱敏人工分类。

## 证据与限制

- 扫描脚本：`artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/scan_workspace_text_credentials.ps1`。
- SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/scan_workspace_text_credentials.ps1` | `578F2F6044DBF3F62DFD22020059F5B14959C24E4EA7289C7FC8215C52A53F65` |
| `fixtures/orders-audit-v1/main.py` | `8559DE9BEFF659D172DAAFD806813F11C51B756D1B114ABE548DC65E035187A1` |
| `fixtures/orders-audit-v1/orders.csv` | `FA25D89EDFA82B28B19D1AD0913AA44759D4C4C39516DC44040C5AD999888E79` |
| `fixtures/orders-audit-v1/README.md` | `827CC97EB5594A9F693D8CA560C8A1E83A47ED84DF9D236B6EA305628B18C141` |

- 扫描结果只覆盖已列扩展名、目录和模式；无法证明项目里没有任何凭据，也不处理编码、拆分、混淆、未知 token 格式或运行时输入。
- 此扫描不提供 API 对学生提交快照的秘密内容检测，不会阻止敏感文本被提交。当前任务只验证固定合成 fixture 和工作区静态内容。
- 不得据此声称生产凭据管理或学生资料防泄漏已经通过。
- 本扫描未启动服务、浏览器、模型、网络调用或代码执行；未改代码逻辑。

## 后续

合同中“Artifact allowlist 与凭据扫描”的静态扫描证据已补齐；生产级凭据检测/防泄漏仍不在本次范围。继续 P4 必须先具备合规预览路径，再对合成数据运行 HTTP/浏览器验证。Foundation Spike、生产身份、真实数据和部署状态均未改变。

## Git

- 当前分支：`codex/r0-teacher-task-authoring`。
- 修改：本报告、扫描脚本、合同验收说明和当前状态追加记录。
- Commit：`NONE`。
