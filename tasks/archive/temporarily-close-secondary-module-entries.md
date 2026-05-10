# 暂时关闭第二、第三模块入口

## Objective

暂时关闭 `Support Copilot` 和 `Job Assistant` 的普通用户入口，让当前产品只开放 `AI 热点追踪`。

## Scope

- 主页模块入口中保留 `Support Copilot` 和 `Job Assistant` 的展示，但改为不可点击的暂停状态。
- 防止前端继续通过主页为 `support` 或 `job` 创建新工作区。
- 已存在的 `support` 或 `job` 工作区仍可从历史记录进入，但只显示暂未开放说明，不进入旧工作台或任务面板。
- 不删除模块代码，不删除历史数据，不改模块产品名。

## Verification

- `npm --prefix web run verify`
- 手工检查主页 support/job 入口不可点击，已有 support/job 工作区不再进入旧模块工作台。
