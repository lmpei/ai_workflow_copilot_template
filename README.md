# AI Workflow Copilot

AI Workflow Copilot 是一个以学习为导向的 AI 工作流工作台项目。它用同一套共享平台核心，承载三个场景模块：

- Research Assistant
- Support Copilot
- Job Assistant

这个仓库的目标，不只是做出一个能聊天的 AI 页面，而是尽可能把现代 AI 应用里常见的实现逻辑真正做一遍：
文档接入、检索增强、异步任务执行、评测、追踪，以及场景化工作流界面。

> 当前真实状态
>
> 本地栈现在已经可以正常运行。`Stage D` 正在把它推进成真正可公开访问的互联网 demo。
> 但公网 URL 和面向小白用户的点击即用入口还没有正式上线，所以这份 README 会明确区分“现在已经有的”与“还在准备中的”。

## 30 秒内你应该理解什么

- 这不是一个单聊天机器人项目，而是一个共享工作流平台。
- 平台已经具备：认证、工作区、文档接入、Grounded Chat、异步任务、评测与可观测性。
- `Research` 目前仍然是最深的参考工作流；`Support` 和 `Job` 也已经在 Stage C 完成了结构化流程深度。
- `Stage D` 的重点是：公网 demo 入口、展示路径更清晰，以及 demo 级别的安全边界和操作约束。

## 从这里开始

| 入口 | 面向对象 | 状态 | 你会得到什么 |
| --- | --- | --- | --- |
| [开发者本地体验](#开发者本地体验) | 开发者、技术面试官、技术协作者 | 现在可用 | Windows 一键启动 + 标准 Docker Compose 启动路径 |
| [公网 Demo / 招聘展示入口](#公网-demo--招聘展示入口) | 小白用户、招聘方、非技术评审 | 预留占位 | 未来真实的公网 URL、登录入口和引导演示路径 |

## 开发者本地体验

### Windows 最快路径

1. 运行本地 demo 启动脚本：

```powershell
cmd /c scripts\start-local-demo-windows.cmd
```

2. 如果是第一次运行且仓库里还没有 `.env`，脚本会先自动创建 `.env`，然后停止。
3. 打开 `.env`，把 `AUTH_SECRET_KEY=replace_me` 换成你自己的真实 secret。
4. 再次运行同一条命令。
5. 等容器启动完成后，打开：

- 前端：`http://localhost:3000`
- API：`http://localhost:8000/api/v1`
- 健康检查：`http://localhost:8000/api/v1/health`

这个脚本会做这些事：

- 如果缺少 `.env`，就从 `.env.example` 复制一份
- 如果 `AUTH_SECRET_KEY` 还是默认占位值，就明确停止并提示你修改
- 调用现有的 Windows setup helper
- 最后执行 `docker compose up --build`

### 手动跨平台路径

如果你不想用 Windows 一键脚本，也可以走标准路径：

```bash
cp .env.example .env
# 编辑 .env，把 AUTH_SECRET_KEY 改掉
docker compose up --build
```

Windows 依赖准备脚本：

```powershell
cmd /c scripts\setup-windows.cmd
```

Windows 验证脚本：

```powershell
cmd /c scripts\verify-windows.cmd
```

## 公网 Demo / 招聘展示入口

这是以后给非技术用户、招聘方、面试官直接使用的入口。

- 公网 demo URL：`Stage D 中，暂未上线`
- 公网注册 / 访客入口：`Stage D 中，暂未上线`
- 引导式 showcase 路径：`Stage D 中，暂未上线`

这个入口未来应该做到：

- 打开一个真实公网地址
- 通过受控的 public-demo 路径登录或注册
- 落到一个清晰的工作区引导流程，而不是空页面
- 展示真实的工作流深度，而不是只有 UI 壳子
- 让用户直接看到当前 demo 的限制，而不是靠隐藏的运维假设撑着

在这个入口正式上线之前，最诚实的体验方式仍然是上面的本地体验路径。

## 现在这个项目已经能做什么

| 模块 | 当前已具备能力 | 典型输出 |
| --- | --- | --- |
| Research Assistant | 文档上传、Grounded Chat、结构化研究任务、Research 资产保存、版本比较 | 摘要、报告、带证据的研究结果 |
| Support Copilot | Grounded case intake、回复草稿、case follow-up、escalation packet | 分诊结论、回复草稿、升级交接包 |
| Job Assistant | 结构化招聘评审、候选人比较、shortlist 生成 | 匹配评估、候选人 shortlist、面试关注点 |

## 平台层都有哪些能力

三个模块共用同一套平台能力：

- 认证与会话管理
- 工作区与模块切换
- 文档上传、解析、切块、向量化和检索
- Grounded Chat 与引用
- 异步任务与 worker 执行
- Eval dataset、eval run 与结果查看
- Trace、metrics 和面向操作者的可观测性

高层流程可以理解成：

```text
documents -> retrieval/chat -> tasks -> evals/traces -> module-specific workflow outputs
```

## 展示边界

这个项目已经不小了，但 README 不应该夸大它。

现在真实成立的事：

- 本地开发与验证是完整可运行的
- `Stage D` 的 public-demo guardrails 已经落地
- 三个模块共用同一套 runtime，而不是三套孤立应用
- 系统已经具备 RAG、工作流执行、评测和结构化模块流程

现在还不成立的事：

- 公网互联网 demo 还没有正式上线
- 它还不是一个 production-grade SaaS 平台
- 企业认证、计费、重度防滥用能力不在当前范围内
- 一些更深的产品化工作，尤其是非 Research 的 workbench 持久层，还属于后续阶段

当前 public-demo 的规则说明见：`docs/development/PUBLIC_DEMO_BASELINE.md`

## 仓库结构

- `server/`
  - FastAPI API、services、repositories、workers、tests
- `web/`
  - Next.js 应用、路由页面和共享 UI 组件
- `docs/`
  - 长文档：产品、架构、开发、review
- `tasks/`
  - 当前任务和归档任务
- `scripts/`
  - 本地准备、验证、发布辅助脚本

## 如果你想继续往下读

建议先看这些文件：

- `STATUS.md`
  - 当前目标、阻塞点、active task
- `ARCHITECTURE.md`
  - 架构速览
- `docs/prd/STAGE_D_PLAN.md`
  - 当前阶段计划：公网 demo baseline
- `docs/prd/LONG_TERM_ROADMAP.md`
  - 更长远的学习和能力演进路线
- `docs/development/PUBLIC_DEMO_BASELINE.md`
  - 当前 public-demo 的限制和操作者规则

## 验证命令

后端基线：

```powershell
cd server
..\.venv\Scripts\python.exe -m pytest tests
```

前端基线：

```powershell
cmd /c npm --prefix web run verify
```