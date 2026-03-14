from app.core.config import get_settings
from app.core.queue import build_redis_settings
from app.services.task_execution_service import run_task_execution


async def run_platform_task(ctx: dict[str, object], task_id: str) -> dict[str, object]:
    return run_task_execution(task_id)


class WorkerSettings:
    functions = [run_platform_task]
    redis_settings = build_redis_settings()
    queue_name = get_settings().task_queue_name
