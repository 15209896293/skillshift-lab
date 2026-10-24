# R0 本机网页原型验证报告

- Task ID：`R0-LOCAL-WEB-PROTOTYPE-001`
- Gate：Gate A 产品交互扩展；Gate B 仍为 PARTIAL。
- 日期：2026-09-24。
- 结论：**PASS（仅限本机、合成、确定性、无外部服务范围）**。

## 已验证事实

1. 教师可在本机页面创建冻结合成任务，学生可开始任务、查看任务状态、请求确定性引导并提交任务关联响应。
2. 教师可在页面查看最新提交，发送认可、请求说明、请求补正或环境问题反馈；领域状态机仍拒绝越权与非法转换。
3. 端到端测试覆盖创建 → 开始 → 引导 → 提交 → 请求说明 → 补交 → 认可 → `CLOSED` Manifest。
4. API 只使用固定合成角色 `teacher-demo` 和 `student-demo`，数据仅保存在进程内。静态资源有固定白名单，启动入口固定绑定 `127.0.0.1`。
5. 已进行一次短时浏览器检查：页面显示教师/学生边界；真实操作达到 `CLOSED`。检查后页面已关闭，回环服务已停止。

## 执行的验证

```text
python -m compileall -q apps\agent-first
python -m unittest discover -s tests -p 'test_local_web_prototype.py' -v
python -m unittest discover -s tests -p 'test_agent_first_vertical_slice.py' -v
python -m unittest discover -s tests -p 'test_domestic_model_gateway_contract.py' -v
python -m unittest discover -s tests -p 'test_deepseek_contract.py' -v
python -m unittest discover -s tests -p 'test_deepseek_runtime_contract.py' -v
python -m unittest discover -s tests -p 'test_school_budget_contract.py' -v
git diff --check
```

结果：编译通过；网页原型 5/5、Gate A 7/7、模型网关 6/6、DeepSeek 请求契约 4/4、DeepSeek 运行时接缝 4/4、学校预算许可 5/5，合计 **31/31** 测试通过；`git diff --check` 通过。上述运行均不发起真实网络或模型调用。

## 可复核哈希（SHA-256）

| 文件 | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/local_web.py` | `755E6EBA5574D80B510DA5086358560DDAD84E627F69AABDB378E7646683A634` |
| `apps/agent-first/run_local_web.py` | `CBD944E5185D57F964648611728FA09E741DDC937FB56720D56E2E42991CE157` |
| `apps/agent-first/web/index.html` | `B76D3DEC1C44D6EBCBAAEE0BB97226B44BE4B7B065A2971DF62AF12BE1A53CF9` |
| `apps/agent-first/web/app.js` | `B52B8A667396A735B4042AC696C6DE53E50AF34BD08B53A4F3D3A6EB050526F4` |
| `apps/agent-first/web/styles.css` | `AFCAE85CD8F8B719A0F242BD69B238326699DF848B971DB5193BDB2131B12D7C` |
| `tests/test_local_web_prototype.py` | `112D48C475DFD8A59FD4C97AF94C9BC6DDD2576FCEB6848146AAED60A7473CA0` |

## 限制与后续门槛

- 这不是生产前后端：没有登录、真实权限、数据库、并发保护、跨进程账本、持久提交、可恢复服务或真实课程数据。
- 这不是模型集成：页面仍使用确定性 `ScriptedGuidanceAdapter`，不读取 Key、不解析预算许可、不调用 DeepSeek。
- 这不是部署验证：未连接 ECS、未开放端口、未配置域名/HTTPS/密钥服务/数据库，也未执行部署。
- 下一阶段应先以独立规格定义生产 API 身份边界、持久任务/预算账本和密钥服务接缝；发生真实数据、真实模型或部署需求时须再次决策。

## 页面刷新恢复校正（2026-09-24）

- Task ID：`R0-LOCAL-WEB-REFRESH-RECOVERY-001`。
- 发现原页面提示“刷新或重启后清空”，但任务只存在服务进程内；浏览器刷新会丢失 JavaScript 中的 assignment ID，却不会清空服务端进程内任务，造成页面无法恢复任务且提示不准确。
- 修正：前端启动时 GET `/api/assignments` 并恢复最近的合成任务；不写 localStorage/sessionStorage；页面提示改为“刷新会重新载入最近任务，重启服务才会清空”。规格增加 LWP-07。
- 验证：`test_local_web_prototype.py` 6/6 PASS；后续全量回归 `python -m unittest discover -s tests` 为 101 项、100 PASS、1 个既有 skip；Windows isolation 模块单独复跑 7/7 PASS。`compileall`、`node --check`、`git diff --check` 通过。Node mock DOM/API 冒烟通过；随后在短时本机浏览器会话创建 `assignment-1`、刷新页面，浏览器可访问本机 API 并恢复最近任务及 `ASSIGNED` 状态。服务绑定 `127.0.0.1:8765`，查看后当轮以 Ctrl+C 停止，临时浏览器标签已关闭；没有外网请求。
- 视觉限制：本次真实浏览器核对使用可访问性树确认恢复后的标题和状态，未保存或检查截图；该检查不是完整的视觉/响应式 QA。
- 限制：只恢复当前本机进程内最近一项合成任务，不是账号隔离、跨用户视图、数据库持久化或生产恢复机制。
- 本次页面/测试 SHA-256：`web/app.js` `983DA1FFB9B5338DF6D4320A4D28E4BCCD4D7B0D31792D4FB35561CE054967D6`；`web/index.html` `C8223CAC5423C06AF265B984EA8CD867B95B0515B645531F45E7BF5FB77A487B`；`tests/test_local_web_prototype.py` `1F76481B69CDD8AB75EDE9F5D85A751C12F3EBF97CEBCEAE34857FEB034B17B2`。
- Commit：`NONE`。

## 教师任务文字配置扩展（2026-09-24）

- Task ID：`R0-TEACHER-TASK-AUTHORING-001`；独立规格见 `specs/R0-TEACHER-TASK-AUTHORING/README.md`。
- 本机网页现在允许教师在固定结构的合成模板上编辑标题、目标、学生责任和提交要求；字段有非空及 UTF-8 字节上限，API 严格拒绝未声明字段。协作方式仍固定为“引导需确认”；没有新增上传、评分、身份、持久化、模型或外网能力。
- `test_local_web_prototype.py` 更新为 8/8 PASS，Agent-first 领域回归 8/8 PASS；其后全量套件 103 项、102 PASS、1 SKIP，退出码 0。编译、Node 语法、`git diff --check` 均 PASS。
- 短时浏览器检查实际编辑并创建 `assignment-1`，教师与学生页展示相同的四字段任务；刷新后最近任务及 `ASSIGNED` 状态恢复。已检查页面截图和无障碍树。回环服务会话已 Ctrl+C 结束；结束后只观察到一个不同 PID 的 IPv6 wildcard 本地 `http.server` 监听，路径属于另一项目，未触碰/停止该进程。当前原型仍没有认证，不得接收真实数据。
- 页面输入只用本次构造的合成任务，没有发送到外网；截图未保存为项目 Artifact。
