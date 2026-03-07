def schedule_classification(task_id: str) -> dict:
    return {
        "task_id": task_id,
        "worker": "classification",
        "status": "queued",
    }
