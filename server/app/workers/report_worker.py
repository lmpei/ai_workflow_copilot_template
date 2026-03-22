"""Scaffold-only report worker helpers.

This file is not registered in WorkerSettings and does not represent a live
async entrypoint yet.
"""


def schedule_report(task_id: str) -> dict:
    """Return the planned queue payload shape for a future report worker."""
    return {
        "task_id": task_id,
        "worker": "report",
        "status": "queued",
    }