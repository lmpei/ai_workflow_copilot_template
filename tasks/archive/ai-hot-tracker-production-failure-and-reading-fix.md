# AI 热点追踪生产失败与阅读区修复

## Objective

修复公网 `AI 热点追踪` 连续失败的问题，并改善简报阅读区过小、滚动条不可见导致不易阅读的问题。

## Scope

- 修复 `signal_memory` 跨工作区事件主键冲突。
- 保持事件 ID 作为业务语义，数据库主键改为工作区隔离存储键。
- 补回归测试，覆盖两个工作区追踪到同一热点时都能成功。
- 调整热点页面布局，让简报和追问区占满剩余高度。
- 把隐藏滚动条改为可见的细滚动条。

## Verification

- `cd server && ..\.venv\Scripts\python.exe -m pytest tests`
- `npm --prefix web run verify`
