# SkillShift Studio Web（本机合成原型）

本目录是 React 19、TypeScript、Vite 前端工程，包含教师与学生页面，并通过 `/api` 代理访问本机合成 Workspace API。它仍是开发原型；真实身份、生产服务、真实模型、持久化和代码执行均未接通或获准。

## 启动条件

先在仓库根目录启动本机合成 API：

```powershell
python apps/agent-first/run_workspace_api.py --port 8000
```

再在本目录安装依赖并启动前端：

```powershell
npm ci
npm run dev
```

Vite 使用 5173 端口，并将 `/api` 代理到 `http://127.0.0.1:8000`。API 只绑定 loopback，使用进程内存和合成数据；停止服务后数据会清空。教师/学生演示路由不是身份认证。以上启动说明来自配置与脚本静态检查，本次没有现场启动验证。

## 可用脚本

- `npm run dev`：启动 Vite 开发服务器。
- `npm run build`：运行 TypeScript 项目构建检查并生成 Vite 构建产物。
- `npm run lint`：运行 Oxlint。
- `npm run preview`：预览已生成的 Vite 构建产物。

本工程的 build、lint、完整教师/学生浏览器流程和窄屏视觉尚未按 2026-10-09 交接要求现场验证。页面路由与当前边界见仓库 `docs/HANDOFF_STUDIO_WEB_FRONTEND_CONTINUATION_2026-10-09.md`。
