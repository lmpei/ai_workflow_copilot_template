# AI 热点追踪简报生成 payload 稳定化

## Context

切换到 `qwen3.6-plus` 并关闭 thinking mode 后，公网热点追踪仍出现 `report_generation_failed`。线上运行记录显示来源抓取和候选信号已经完成，但简报生成阶段耗时过长后降级。

进一步检查发现，简报生成会把候选 cluster 的完整来源调试信息一起发给模型，包括完整 URL、score breakdown、较长 rank reason，以及同一 cluster 下过多 supporting items。对 `qwen3.6-plus` 来说，这会把 JSON-mode 生成输入撑得过大、过噪，导致生成超时或修复重试失败。

## Scope

- 压缩 report synthesis 输入，只保留生成中文简报需要的最小字段。
- 保留后端 source items 的完整 URL 和引用信息，不影响前端来源锚点渲染。
- 增加回归测试，防止调试字段重新进入模型输入。
- 同步控制面文档并归档本任务。

## Verification

- `cd server && ..\.venv\Scripts\python.exe -m pytest tests\test_ai_hot_tracker_report_service.py tests\test_model_interface_service.py`
- 部署后用公网运行记录复测简报生成阶段。
