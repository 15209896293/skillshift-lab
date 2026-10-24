# 合成控制面持久化契约验证报告

- Task ID：`R0-SYNTHETIC-CONTROL-PLANE-PERSISTENCE-001`
- Gate：Gate B 控制面基础；Gate B 总体仍为 PARTIAL。
- 结论：**PASS（仅限合成、本机 SQLite 契约）**。

## 已验证事实

1. 冻结合成任务 Manifest 可追加保存，关闭并重开临时 SQLite 数据库后仍可按修订读取。
2. 相同 `command_id` 与相同内容返回原回执，不产生第二次写入；同一命令换内容会明确拒绝，既有历史不被覆盖。
3. 非合成范围与带凭据特征字段的 Manifest 会被拒绝。
4. 30 个并发合成预算预留尝试中，只有 10 个可各预留 1,000 分，总额严格停在 10,000 分；同一预留命令重试不重复计入。

## 执行验证

```text
python -m compileall -q apps\agent-first
python -m unittest discover -s tests -p 'test_control_plane_persistence.py' -v
python -m unittest discover -s tests -p 'test_local_web_prototype.py' -v
python -m unittest discover -s tests -p 'test_agent_first_vertical_slice.py' -v
python -m unittest discover -s tests -p 'test_school_budget_contract.py' -v
git diff --check
```

结果：编译通过；持久化契约 4/4、网页原型 5/5、Gate A 7/7、既有预算许可 5/5，合计 **21/21** 测试通过；`git diff --check` 通过。无真实网络、模型、密钥或费用。

## 可复核哈希（SHA-256）

| 文件 | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/control_plane_persistence.py` | `6F6279AB1EA0CDAF996E20B21B90F92E7C47B1B2A9C09A76FF74FE25774DAD96` |
| `tests/test_control_plane_persistence.py` | `CBA35823135543086AB790AF678B3226F7837702BA29D577F66A36B4EA59A7C0` |

## 限制

- SQLite 只用于本机合成契约验证，不是生产数据库或生产迁移方案。
- 不含登录、真实身份、真实数据、加密、访问控制、保留/删除、跨服务并发、供应商账单、模型调用或部署。
- 持久预算仅表示预留上限，不表示实际扣费、释放、结算或对账。

下一步必须先形成真实控制面部署前的身份、数据保留、关系数据库、密钥服务和审计规格；不得据此部署或发送真实数据。
