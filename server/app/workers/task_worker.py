"""Live ARQ worker entrypoints.

This module is the active async boundary for task and eval execution. Other
files under server/app/workers are lightweight scaffolds unless they are wired
into WorkerSettings here.
"""
from app.core.config import get_settings
from app.core.queue import build_redis_settings
from app.services.eval_execution_service import run_eval_execution
from app.services.task_execution_service import run_task_execution


async def run_platform_task(ctx: dict[str, object], task_id: str) -> dict[str, object]:
    return run_task_execution(task_id)


async def run_eval_run(ctx: dict[str, object], eval_run_id: str) -> dict[str, object]:
    return run_eval_execution(eval_run_id)


class WorkerSettings:
    functions = [run_platform_task, run_eval_run]
    redis_settings = build_redis_settings()
    queue_name = get_settings().task_queue_name
