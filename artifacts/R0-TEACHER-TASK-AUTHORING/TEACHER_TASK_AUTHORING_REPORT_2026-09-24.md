# 教师任务文字配置扩展报告

- Task ID：`R0-TEACHER-TASK-AUTHORING-001`
- Gate：Gate A；范围为本机、固定合成角色与数据、确定性引导。
- 结论：**PASS（限合成产品原型）；教师真实工作量尚未验证。**
- 规格：`specs/R0-TEACHER-TASK-AUTHORING/README.md`
- Artifact：`evidence.json`

## 变更

- `apps/agent-first/agent_first/domain.py`：模板结构不变，提供四项文字字段的 UTF-8 字节上限校验。
- `apps/agent-first/agent_first/local_web.py`：任务创建 API 要求固定字段白名单、教师合成角色和完整任务文字；每次创建分配新的合成任务 ID。
- `apps/agent-first/web/index.html`、`app.js`、`styles.css`：教师可在预填样例上编辑任务名称、目标、学生责任和提交要求；教师/学生视图均渲染这些字段并沿用 HTML 转义。
- `tests/test_local_web_prototype.py`：新增自定义文字往返、任务 Manifest 关联、空字段/超长字段/未声明个人字段拒绝测试。
- 更新纵向切片/Web 规格与文档入口；未改供应商、模型运行时、认证、持久化或部署架构。

## 实际验证

```powershell
$env:PYTHONUTF8='1'; python -m compileall -q apps\agent-first
python -m unittest discover -s tests -p 'test_local_web_prototype.py' -v
python -m unittest discover -s tests -p 'test_agent_first_vertical_slice.py' -v
node --check apps\agent-first\web\app.js
python -m unittest discover -s tests
git diff --check
```

- 编译：PASS。
- 网页/API：8/8 PASS；原 Gate A 纵向闭环：8/8 PASS。
- 全量：103 项、102 PASS、1 SKIP，退出码 0。Windows isolation 模块此前独立复跑 7/7 PASS；本次未更改其代码。唯一跳过是 Foundation 的真实目录符号链接攻击，Windows 返回 `WinError 1314`。
- 浏览器：临时启动 `127.0.0.1:8766`；提交自造合成文字创建 `assignment-1`；教师与学生视图显示相同字段；刷新恢复最近任务和 `ASSIGNED` 状态；截图及无障碍树已检查。随后以 Ctrl+C 结束本任务进程。收尾时检测到该端口另有 IPv6 wildcard `http.server` 进程，确认归属另一项目后未触碰。
- 未访问公网、模型、账号、Key、ECS 或真实数据，未产生费用。浏览器截图只用于检查，未写入仓库。

## 限制与风险

- 这验证字段进入 UI/API/Manifest 关联，不验证任务教学设计有效或教师低负担；教师和学生真实身份、授权、跨用户隔离均未实现。
- 任务仍只有固定字段结构与固定“引导需确认”模式，进程重启即清空；真实材料、链接、文件附件和复杂协作规则不在范围内。
- 任务文本按 UTF-8 字节拒绝超限，不静默截断。页面错误是合成原型行为，不应当作生产 API 规范。
- Foundation Spike 仍 PARTIAL，尤其是 OS 级网络隔离、Provider 集成子进程树终止、真实符号链接攻击和服务端同步/重放防护。

## 下一步

产品可用性命题仍待验证：合成浏览器检查不代表真实教师能低负担完成任务创建—复核—补正。后续如要接触教师或收集任何使用记录，先拟定明确、自愿、非计分的验证流程与数据边界，再请求相应授权。真实模型、部署与真实数据仍受各自独立 Gate 限制。

## Git

- 当前分支：`codex/r0-teacher-task-authoring`
- 工作区原有未提交修改和未跟踪文件均保留；本任务只在其上进行范围内编辑。
- Git diff 摘要：新增一项本机合成任务文字配置；API/字段验证与 UI/测试相应更新；新增规格和验证 Artifact。
- Commit：`NONE`。

## SHA-256

| 文件 | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/domain.py` | `36596CB2995851EAF260484863BEEAA064054187B4571359C3161ADEC949814A` |
| `apps/agent-first/agent_first/local_web.py` | `4202FFB727295FA3C3D95E1FB01E4CB035D7D419BEE221691F1C0544BEFC76BA` |
| `apps/agent-first/web/index.html` | `3D84251CF1E3F2E0202AEEFB69E8471BAD008E0DA80C9C77EA7DE20A902E2728` |
| `apps/agent-first/web/app.js` | `BD0E56654186A4E7F7C9FF1844E3150334155788A759B89B43EF3F0FD59C8E56` |
| `apps/agent-first/web/styles.css` | `7EB04726C11EBA033308E22C9DBD453ED4427D2BFC4D64C2FBCE8B5D8F0DBAEB` |
| `tests/test_local_web_prototype.py` | `E0EF599B739F5C6C9B87867E3F8D4247B5917B708BB2DFEC8CA2E0FB14AA8F6F` |
| `evidence.json` | `939A77C4C69DDFB5C0FBEE2A9E621CFAB1BAA16EA5E90D359FF97780B1C8E259` |

本报告自身 SHA-256 由当前主控随状态汇报提供，避免自引用。
