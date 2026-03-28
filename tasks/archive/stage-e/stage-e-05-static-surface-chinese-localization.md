# Task: stage-e-05-static-surface-chinese-localization

## 目标

在不改变模块产品名、模型输出语言和运行时契约的前提下，把当前 live public demo 中用户可见的静态展示文案收敛为中文优先体验。

## 所属阶段

- Stage: Stage E
- Track: 面向 live public demo 的交付与展示收敛

## 为什么现在做

Stage D 已经把系统推进到了真实公网 demo，用户已经可以直接访问 `https://app.lmpai.online`。但当前页面、引导路径、错误提示、demo 模板和部分 seeded 内容仍然混有大量英文，导致整个公开展示面不够统一。继续推进 Support / Job workbench 之前，先完成一轮有边界的中文化，可以把后续演示、面试展示和继续开发的基线收稳。

## 相关上下文

优先参考：

- `STATUS.md`
- `CONTEXT.md`
- `docs/prd/STAGE_E_PLAN.md`
- `tasks/stage-e-02-support-case-workbench-foundation.md`

主要涉及的用户可见表面：

- `web/app/`
- `web/components/`
- `server/app/services/public_demo_showcase_service.py`
- `server/app/schemas/scenario.py`
- 后端中会直接透传到前端显示的用户可见错误字符串

## 精确范围

### 需要完成

1. 前端静态展示文案中文化
- 页面标题
- 区块标题
- 按钮文案
- 表单标签
- placeholder
- empty state / loading state
- 状态 badge
- helper copy / 提示文案

2. guided demo 与 public demo 的内置静态内容中文化
- 模板标题和摘要
- guided showcase 步骤文案
- seeded workspace 标题和描述
- built-in demo path 中的 seeded document 标题、摘要和正文

3. 直接显示到前端的主要后端用户可见错误中文化
- auth
- workspace / public demo
- documents
- tasks
- support / job / research 任务入口的常见用户可见报错

4. scenario registry 中直接展示给用户的静态文案中文化
- 任务标签
- 能力描述
- eval placeholder
- 面板里直接显示的描述性字段

### 明确不做

1. 不修改模型生成内容的语言
2. 不修改 prompt 或任务输出策略
3. 不修改模块产品名
- `Research Assistant`
- `Support Copilot`
- `Job Assistant`
4. 不修改 API 字段名、枚举值、task type、module type、持久化契约
5. 不引入 i18n 框架、locale 切换器或多语言产品范围
6. 不做广泛文档翻译

## 验收标准

1. 主路径页面的静态展示面中文优先
- 首页
- 登录 / 注册
- workspaces
- documents
- chat
- tasks
- modules
- analytics
- eval
- guided demo

2. built-in public demo 路径不再因为模板或 seeded 内容而明显冒出英文静态文案

3. 主路径里常见的用户可见 API 错误不再默认显示英文

4. 三个模块产品名保持不变

5. 模型输出和其他动态用户内容仍保持原状，不被这轮任务误改

## 完成定义

当用户从首页进入 live public demo，并走完“登录 -> workspace -> guided demo -> documents/chat/tasks”主路径时，看到的静态产品表面应当已经是中文优先，且这轮修改不改变现有功能边界。
