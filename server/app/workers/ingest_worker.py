"""Scaffold-only ingest worker helpers.

This file is not registered in WorkerSettings and does not represent a live
async entrypoint yet.
"""


def schedule_ingest(document_id: str) -> dict:
    """Return the planned queue payload shape for a future ingest worker."""
    return {
        "document_id": document_id,
        "worker": "ingest",
        "status": "queued",
    }