def schedule_report(task_id: str) -> dict:
    return {
        "task_id": task_id,
        "worker": "report",
        "status": "queued",
    }
