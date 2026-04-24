# AI 热点追踪 replay corpus 与 judgment calibration

## Why

`AI 热点追踪` 现在线路已经完整，但还缺一个固定、可复跑的判断质量闭环。当前 evaluation 能解释单个 saved run 的排序、聚类、delta 和 grounding 结果，但还不能用一组稳定场景去校准“这轮为什么这样判断”。

## Scope

- 增加一个内部 replay corpus，覆盖：
  - 官方高影响信号优先于老旧开源更新
  - 官方与媒体的同事件保守归并
  - 重复信号进入 steady state 且连续记忆递增
  - 新信号替代旧信号时的 superseded / cooling 语义
- 增加一个 judgment calibration service：
  - 用固定 replay cases 运行当前 decision + delta + signal memory 逻辑
  - 输出每个 case 的 pass/fail 结果和具体 finding
- 补测试，确保 replay suite 可以稳定执行
- 更新控制面文档并归档任务

## Out of Scope

- 不新增消费者可见入口
- 不新增站外通知
- 不新增用户自定义来源
- 不改动热点模块的公开产品定义

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests/test_ai_hot_tracker_decision_service.py tests/test_ai_hot_tracker_replay_service.py tests/test_ai_hot_tracker_tracking_runs.py`
- `npm --prefix web run verify`
