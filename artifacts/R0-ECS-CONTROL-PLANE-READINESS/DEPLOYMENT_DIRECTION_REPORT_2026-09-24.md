# ECS 控制面部署方向报告

- Task ID：`R0-ECS-CONTROL-PLANE-READINESS-001`
- Gate：B（部署方向）
- 状态：**Planned / PARTIAL**

## 已确认的最优方向

1. 现有 ECS 是未来 SkillShift 控制面：平台 API、DeepSeek 网关、预算许可、任务/提交元数据和教师 Web 后端。
2. 不部署本地大模型，不购买 GPU，不让 ECS 运行任意学生代码、Workspace、浏览器自动化或 Shell。
3. DeepSeek Key 将来使用与 ECS 服务身份绑定的托管密钥服务；禁止存入 Git、`.env`、数据库、客户端、日志或 Artifact。
4. 本地内存预算许可只能做测试；真实调用前必须换成持久、原子、可审计的账本。

## 验证

```text
Test-Path docs/adr/ADR-010-ecs-control-plane-and-managed-secret-boundary.md
Test-Path specs/R0-ECS-CONTROL-PLANE-READINESS/README.md
git diff --check
```

结果：文件存在 PASS；文档 diff 检查 PASS。未连接 ECS、未部署、未开端口、未配置密钥或费用。

## 可复核哈希

| 文件 | SHA-256 |
| --- | --- |
| `docs/adr/ADR-010-ecs-control-plane-and-managed-secret-boundary.md` | `99939B5AB390913CF2E07ABAC8A0ED47D60FFC5FEBD56BFD887230EB95A120B6` |
| `specs/R0-ECS-CONTROL-PLANE-READINESS/README.md` | `86DE71275C0576B8198A9D5859A329E481ED37E290611A30B1AFB44A63421EDA` |

## 未关闭项

托管密钥服务、持久预算账本、服务身份、数据库、TLS、网络入口、日志保留、备份、费用告警、合成探针和实际部署均未开始。不得把本方向选择写成服务器已可用。

## Commit

`NONE`

