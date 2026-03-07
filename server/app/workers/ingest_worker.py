def schedule_ingest(document_id: str) -> dict:
    return {
        "document_id": document_id,
        "worker": "ingest",
        "status": "queued",
    }
