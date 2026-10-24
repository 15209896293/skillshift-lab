# DIRECTION-AUDIT-01-R1 证据登记册

审计日期：2026-09-22。证据等级严格分开：**来源真实性**、**文件完整性**、**输出一致性**、**语义正确性**。前三者均不能自动推出第四者，更不能推出学习效果。未安装、启动或实测任何第三方项目。

## 1. 复核命令、工作目录、结果和范围

下列命令均已在本审计会话执行；PowerShell 使用 UTF-8，Python 使用本机工作区依赖运行时。命令仅读取现有文件或调用既有验证器；不写入受保护文件、不启动容器。

| ID | 工作目录 | 完整命令/动作 | 结果 | 检查范围 |
| --- | --- | --- | --- | --- |
| C01 | `F:\比赛\skillshift` | `git -C "F:\比赛\skillshift" status --short --branch`; `git -C "F:\比赛\skillshift" worktree list --porcelain`; `git -C "E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift" status --short --branch` | 主目录 `main`、HEAD `c5d6081`；主目录及 detached worktree 均有未跟踪/未提交文件。 | Git 状态和 worktree 布局；不评价文件内容。 |
| C02 | `F:\比赛\skillshift` | `git diff -- docs/CURRENT_STATE.md`; 读取 `P0A_GATE_PRE_REVIEW.md`、`P0A_CONTROLLED_RECONSTRUCTION_INTERIM_REPORT.md`、`WORKTREE_INTEGRATION_MANIFEST.md`、MySQL README/合同/运行记录。 | 识别对象/范围差异、过期状态风险和 root 账户契约偏差。 | 文本陈述与源码逻辑；不独立见证历史容器运行。 |
| C03 | `F:\比赛\skillshift` | `& $py "...\mysql_contracts\static_contract_check.py"` | `PASS: MySQL controlled-audit artifacts are structurally ready; this static check does not attest runtime execution.` | 必需文件、部分 schema/verifier 文本。 |
| C04 | `F:\比赛\skillshift` | `& $py "...\mysql_contracts\verify_diagnosis.py"` | PASS。 | 诊断文件是否含六个固定词/数字；不检查 SQL/论证。 |
| C05 | `F:\比赛\skillshift` | `& $py "...\mysql_contracts\verify_tsv.py" --actual "...\P0A-PUB-002\out\daily_paid_summary.tsv" --expected "...\P0A-PUB-002\expected\daily_paid_summary.tsv"` | `PASS: exact result matches daily_paid_summary.tsv.` | 当前 TSV 与同包预期文本一致。 |
| C06 | `F:\比赛\skillshift` | `& $py "...\controlled_runs\P0A-PUB-008_csv_cleaning\verify.py" --clean-output "...\out\cleaned_students.csv" --report-output "...\out\quality_report.json"` | PASS。第一次误传 `--cleaned-output` 只得到 usage 错误且未写文件；随后以此正确参数 PASS。 | 当前 CSV/JSON 与同包预期一致。 |
| C07 | `F:\比赛\skillshift` | `& $py "...\controlled_runs\P0A-PUB-009_multi_source_merge\verify.py" --merged-output "...\out\merged_enrollments.csv" --report-output "...\out\reconciliation_report.json"`; `& $py "...\controlled_runs\P0A-PUB-010_user_behavior_pipeline\verify.py" --daily-output "...\out\daily_indicators.csv" --report-output "...\out\quality_report.json"` | 两项 PASS。 | 当前结构化输出与同包预期一致。 |
| C08 | `F:\比赛\skillshift` | `& $py "...\artifacts\P0-A\verify_evidence_manifest.py"` | `PASS: verified 76 P0-A evidence entries.` | 隔离 worktree 内清单所列 76 文件的哈希/字节集合。 |
| C09 | `F:\比赛\skillshift` | 读取 `run_controlled_audits.ps1`，定位 `mysql -uroot`、`CREATE DATABASE`、无 `CREATE USER`/`GRANT`。 | 脚本以 root 执行候选提交/查询，与合同非特权任务用户要求不一致。 | 运行脚本行为设计；未重跑脚本或容器。 |
| C10 | `F:\比赛\skillshift` | `git ls-remote https://github.com/trampgeek/moodle-qtype_coderunner.git HEAD` | `Recv failure: Connection was reset`。未重试、未得到 commit SHA。 | 远端 HEAD 版本锚定失败；不得填充猜测 SHA。 |
| C11 | `F:\比赛\skillshift` | 读取三份交付文件并用 UTF-8 脚本检查确为三个 `.md`、指定标题存在、无行尾空白；`git diff --check`；`git status --short`。 | 结构检查 PASS；本任务目录未跟踪，其他既有未提交文件仍保持不动。 | 交付集合和空白错误；不评价 Markdown 内容的学术正确性。 |

`$py` 为 `C:\Users\lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`。表中的 `...` 仅为扫描便利；下列是 C03–C08 实际可复制的完整命令（不包括此前已经完成、且本轮没有重跑的容器脚本）：

```powershell
$py = 'C:\Users\lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\static_contract_check.py'
& $py 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\verify_diagnosis.py'
& $py 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\verify_tsv.py' --actual 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\P0A-PUB-002\out\daily_paid_summary.tsv' --expected 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\P0A-PUB-002\expected\daily_paid_summary.tsv'
& $py 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\controlled_runs\P0A-PUB-008_csv_cleaning\verify.py' --clean-output 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\controlled_runs\P0A-PUB-008_csv_cleaning\out\cleaned_students.csv' --report-output 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\controlled_runs\P0A-PUB-008_csv_cleaning\out\quality_report.json'
& $py 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\controlled_runs\P0A-PUB-009_multi_source_merge\verify.py' --merged-output 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\controlled_runs\P0A-PUB-009_multi_source_merge\out\merged_enrollments.csv' --report-output 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\controlled_runs\P0A-PUB-009_multi_source_merge\out\reconciliation_report.json'
& $py 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\controlled_runs\P0A-PUB-010_user_behavior_pipeline\verify.py' --daily-output 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\controlled_runs\P0A-PUB-010_user_behavior_pipeline\out\daily_indicators.csv' --report-output 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\controlled_runs\P0A-PUB-010_user_behavior_pipeline\out\quality_report.json'
& $py 'E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\verify_evidence_manifest.py'
```

这些命令分别得到 C03–C08 所列 PASS；它们的范围仍仅为静态结构、当前输出一致性和 manifest 完整性。

## 2. 本地证据的性质

| ID | 证据位置 | 核验类别 | 支持什么 | 不支持什么 |
| --- | --- | --- | --- | --- |
| L01 | `F:\比赛\skillshift` 与 `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift` 的 Git 元数据 | 文件完整性/交接状态 | 两份未冻结工作区及 HEAD/状态。 | 文件真伪、内容正确或可合并性。 |
| L02 | 主目录 `docs/CURRENT_STATE.md`（未提交 diff） | 状态陈述 | 主目录作者当时如何描述前五项。 | 隔离 worktree 重建不曾发生。 |
| L03 | 隔离 worktree `artifacts/P0-A/P0A_CONTROLLED_RECONSTRUCTION_INTERIM_REPORT.md`、`P0A-PUB-001/002/RUN_RECORD.md` | 运行陈述/来源真实性待补 | 文件记录合成重建、时间、环境和输出。 | 无独立日志/镜像/见证时的历史运行真实性。 |
| L04 | `artifacts/P0-A/mysql_contracts/README.md`、`run_controlled_audits.ps1`、`P0A-PUB-001/002/task_contract.md` | 契约/源码语义核查 | 文档要求非特权账户，脚本实际使用 root；描述存在过期和同对象偏差。 | 任何权限边界已被满足。 |
| L05 | `...\mysql_contracts\verify_diagnosis.py` | 源码语义核查 | 验证器是固定词项检查。 | 对诊断逻辑的有效测量。 |
| L06 | `...\mysql_contracts\static_contract_check.py`、`verify_tsv.py`、`controlled_runs/*/verify.py` | 输出一致性 | 当前输出满足当前预期文件/文件结构。 | 预期值独立正确、未见变体有效、学生能力。 |
| L07 | `...\EVIDENCE_MANIFEST.json` 与 `verify_evidence_manifest.py` | 文件完整性 | 76 项文件哈希/字节匹配该 manifest。 | 来源真实性、语义正确性、因果结论。 |
| L08 | `task_inventory_public_seed.md`、`PUBLIC_SOURCE_VERIFICATION.md` | 公开来源可追溯性 | 公开任务模式/教程支持。 | 是本地历史任务或本校 rubric。 |
| L09 | `wenben\SkillShift_Lab_项目立项书暨研究开发文档_V2.2.docx`，章节“项目定位与价值闭环”“13.1 V2.2 的 P0 证据验证路线”“开发闸门” | 原始战略文件只读提取 | 自主使用、设备公平和 P0 闸门属于计划约束。 | 这些计划假设已经得到真实数据支持。 |

## 3. 公开来源、定位依据和核验状态

所有仓库为**默认分支文件定位**，而非不可变 commit；C10 远端 SHA 查询失败。许可证只有在仓库 LICENSE/官方条款实际核读后才作临时标注，未完成的均写“待核实”。

| ID | 来源与定位依据 | 核验方式/状态 | 支持什么 | 待核实或不支持什么 |
| --- | --- | --- | --- | --- |
| W01 | [CodeRunner](https://github.com/trampgeek/moodle-qtype_coderunner)：`master/README.md`、`master/version.php`、`master/LICENSE` | 仓库页/源码文件核查。README 版本、仓库标签与源码许可证头部存在需法律核读的差异。 | Moodle 沙箱测试/自动评分的存在。 | 最终许可证、commit SHA、本机运行和教育效果。 |
| W02 | [PrairieLearn](https://github.com/PrairieLearn/PrairieLearn)：`master/README.md`、`master/LICENSE`、`master/docs/installing.md` | 仓库/官方安装文档。 | 自动题、grader、Docker/WSL2 运维要求。 | 本地部署、总拥有成本、学习效果。 |
| W03 | [Dify](https://github.com/langgenius/dify)：`main/README.md`、`main/LICENSE` | 仓库/许可证核查。 | Agent 工作流和附条件开源许可。 | 教育测量有效性、无条件商用/多租户。 |
| W04 | [AgentBench](https://github.com/THUDM/AgentBench)：`main/README.md`、`main/LICENSE`、`main/extra/docker-compose.yml` | 仓库源码核查。 | Agent 基准与容器化环境。 | 对学生能力的测量、低运行成本。 |
| W05 | [DB-GPT](https://github.com/eosphoros-ai/DB-GPT)：`main/README.md`、`main/LICENSE`、`main/pyproject.toml` | 仓库源码核查。 | 数据 Agent、SQL/Python、数据源/沙箱能力，MIT 标注。 | 学生训练效果、安全配置已充分验证。 |
| W06 | [Great Expectations](https://github.com/fivetran/great_expectations)：`develop/README.md`、`develop/LICENSE`、`develop/pyproject.toml` | 仓库源码核查。 | 数据合同/验证报告能力与 Python 版本提示。 | 在本机 Python 3.14 的稳定支持、学习量规。 |
| W07 | [Codio 自动评分](https://www.codio.com/features/auto-grading) | 官方产品页。 | 标准/高级测试、量规与参数化任务的宣称。 | 价格、SLA、数据条款和独立效果。 |
| W08 | [Skillable 白皮书](https://www.skillable.com/wp-content/uploads/2023/04/Skillable-Whitepaper-Evolving-Hands-on-Labs-with-AI.pdf)，第 13 页 | 厂商 PDF。 | 厂商讨论动态评分/AI 实验。 | 独立效果、价格、部署质量。 |
| CN01 | [清华 AI 通识教育红皮书](https://aige.cs.tsinghua.edu.cn/redbook/) | 官方公开材料。 | 核查证据、比较输出/反思依赖作为教育方向线索。 | SQL 产品或因果效果。 |
| CN02 | [教育智能体辅助实验教学的风险识别与过程监管研究](https://www.sy.uestc.edu.cn/article/doi/10.12179/1672-4550.20260095) | 论文页面/摘要核查。 | 审查义务、过程监管和编程实验案例是直接相关研究线索。 | 原始数据、量规、高职 SQL 外推。 |
| CN03 | [反向验证增强的 SQL 优化生成方法](https://wuj.whu.edu.cn/zh/article/doi/10.14188/j.1671-8836.2025.0215/) | 期刊摘要核查。 | SQL 语义偏差与反向验证是直接技术问题。 | 学生训练或教学效果。 |
| CN04 | [text-sql](https://github.com/ALbum3270/text-sql)：默认分支 `README.md` | 仓库 README 线索。 | SQL validation/self-correction 原型线索。 | 作者/维护、许可证、commit SHA、可复现性和教育用途均待核。 |
| CN05 | [编程能力元分析](https://xdjylc.scnu.edu.cn/cn/article/id/25b4918b-630e-4be9-9dc6-6ac2fea19b43?viewType=HTML) | 论文摘要核查。 | 编程教育结果异质、深度认知需关注的背景。 | 未获取全文方法时的效应量或本地结论。 |
| R01 | [Bassner et al.](https://doi.org/10.1016/j.caeai.2025.100537) | 同行评议论文摘要。 | 特定 CS1 中任务表现与学习可分离。 | 高职 SQL 的预测。 |
| R02 | [Li, Liu & Dong](https://doi.org/10.14742/ajet.9932) | 同行评议论文。 | 自我导向 GenAI 编程学习与迁移风险的背景。 | SkillShift 成效。 |
| R03 | [ETS AI/数字素养评估报告](https://www.tr.ets.org/content/dam/ets-org/pdfs/rd/ets-digital-literacy-ai-full-report.pdf) | 报告第 25 页附近。 | 多过程/产出证据与解释透明度原则。 | 本项目量规已有效。 |
| C01 | [挑战杯规则页](https://www.tiaozhanbei.net/rules) | 官方规则页。 | 公开的作品类别及 AI 代写违规风险。 | 未来届次。 |
| C02 | [2025 章程 PDF](https://2025.tiaozhanbei.net/media/ckeditor_uploads/49/2025/06/13/1.%E2%80%9C%E6%8C%91%E6%88%98%E6%9D%AF%E2%80%9D%E5%85%A8%E5%9B%BD%E5%A4%A7%E5%AD%A6%E7%94%9F%E8%AF%BE%E5%A4%96%E5%AD%A6%E6%9C%AF%E7%A7%91%E6%8A%80%E4%BD%9C%E5%93%81%E7%AB%9E%E8%B5%9B%E7%AB%A0%E7%A8%8B.pdf) | 官方 2025 PDF。 | 2025 的资格、时间窗、类别、公示/审核。 | 2026+ 的规则、用户个人资格、类别选择。 |
