"""Scaffold-only classification worker helpers.

This file is not registered in WorkerSettings and does not represent a live
async entrypoint yet.
"""


def schedule_classification(task_id: str) -> dict:
    """Return the planned queue payload shape for a future classification worker."""
    return {
        "task_id": task_id,
        "worker": "classification",
        "status": "queued",
    }