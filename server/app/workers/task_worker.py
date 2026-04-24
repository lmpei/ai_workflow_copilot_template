"""Live ARQ worker entrypoints.

This module is the active async boundary for task, eval, and bounded research-analysis execution.
Other files under server/app/workers are lightweight scaffolds unless they are wired into WorkerSettings here.
"""
from arq import cron

from app.core.config import get_settings
from app.core.queue import build_redis_settings
from app.services.ai_hot_tracker_tracking_service import run_ai_hot_tracker_tracking_sweeper
from app.services.eval_execution_service import run_eval_execution
from app.services.research_analysis_run_service import run_research_analysis_run_execution
from app.services.task_execution_service import run_task_execution


async def run_platform_task(ctx: dict[str, object], task_id: str) -> dict[str, object]:
    return run_task_execution(task_id)


async def run_eval_run(ctx: dict[str, object], eval_run_id: str) -> dict[str, object]:
    return run_eval_execution(eval_run_id)


async def run_research_analysis_run(ctx: dict[str, object], run_id: str) -> dict[str, object]:
    return run_research_analysis_run_execution(run_id)


async def run_ai_hot_tracker_sweeper(ctx: dict[str, object]) -> dict[str, object]:
    return run_ai_hot_tracker_tracking_sweeper()


class WorkerSettings:
    functions = [run_platform_task, run_eval_run, run_research_analysis_run, run_ai_hot_tracker_sweeper]
    cron_jobs = [
        cron(
            run_ai_hot_tracker_sweeper,
            minute={0, 15, 30, 45},
            second=0,
        )
    ]
    redis_settings = build_redis_settings()
    queue_name = get_settings().task_queue_name
