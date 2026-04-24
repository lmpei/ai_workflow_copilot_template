# AI 热点追踪 replay evaluation surface

## Why

`AI 热点追踪` 已经有固定 replay corpus 和 judgment calibration，但这套能力还只存在于后端测试与内部服务里。为了让热点模块的 internal evaluation 真正成为判断质量工作台，而不是只看单个 saved run，需要把 replay suite 作为只读内部视图接进系统。

## Scope

- 新增一个内部 replay evaluation API
- 让 `?view=evaluation` 可以读取 replay suite 总览
- 在内部评测视图里展示 replay suite 的总体状态、每个 case、以及失败 finding
- 补接口测试与前端基线验证
- 同步控制面文档并归档任务

## Out of Scope

- 不改动消费者主路径
- 不新增普通用户入口
- 不改动热点模块的公开产品定义

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests/test_ai_hot_tracker_replay_service.py tests/test_ai_hot_tracker_tracking_runs.py`
- `npm --prefix web run verify`
