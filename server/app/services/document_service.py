def get_document_module_status() -> dict:
    return {
        "status": "scaffolded",
        "next_step": (
            "Add the document API surface in Phase 1, then implement upload storage, "
            "parsing, chunking, and vector indexing in Phase 2."
        ),
    }
