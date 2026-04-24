from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import session_scope
from app.models.ai_hot_tracker_signal_memory import AiHotTrackerSignalMemory


def list_workspace_ai_hot_tracker_signal_memories(
    *,
    workspace_id: str,
) -> list[AiHotTrackerSignalMemory]:
    with session_scope() as session:
        statement = (
            select(AiHotTrackerSignalMemory)
            .where(AiHotTrackerSignalMemory.workspace_id == workspace_id)
            .order_by(AiHotTrackerSignalMemory.last_seen_at.desc())
        )
        return list(session.scalars(statement).all())


def upsert_workspace_ai_hot_tracker_signal_memories(
    *,
    workspace_id: str,
    records: list[dict[str, object]],
) -> list[AiHotTrackerSignalMemory]:
    if not records:
        return []

    now = datetime.now(UTC)
    event_ids = [
        record["event_id"]
        for record in records
        if isinstance(record, dict) and isinstance(record.get("event_id"), str)
    ]
    if not event_ids:
        return []

    with session_scope() as session:
        existing = {
            item.id: item
            for item in session.scalars(
                select(AiHotTrackerSignalMemory).where(
                    AiHotTrackerSignalMemory.workspace_id == workspace_id,
                    AiHotTrackerSignalMemory.id.in_(event_ids),
                )
            ).all()
        }

        stored: list[AiHotTrackerSignalMemory] = []
        for record in records:
            event_id = record.get("event_id")
            if not isinstance(event_id, str):
                continue

            memory = existing.get(event_id)
            if memory is None:
                memory = AiHotTrackerSignalMemory(
                    id=event_id,
                    workspace_id=workspace_id,
                    created_at=now,
                )

            memory.fingerprint = str(record.get("fingerprint") or event_id)
            memory.title = str(record.get("title") or "Untitled signal")
            memory.category = str(record.get("category") or "models")
            memory.first_seen_at = record.get("first_seen_at") or now
            memory.last_seen_at = record.get("last_seen_at") or now
            memory.continuity_state = str(record.get("continuity_state") or "continuing")
            memory.activity_state = str(record.get("activity_state") or "continuing")
            memory.source_families_json = list(record.get("source_families") or [])
            memory.source_item_ids_json = list(record.get("source_item_ids") or [])
            memory.source_labels_json = list(record.get("source_labels") or [])
            memory.latest_priority_level = str(record.get("latest_priority_level") or "low")
            memory.latest_rank_score = float(record.get("latest_rank_score") or 0.0)
            memory.last_seen_run_id = (
                str(record["last_seen_run_id"]) if record.get("last_seen_run_id") else None
            )
            memory.streak_count = int(record.get("streak_count") or 0)
            memory.cooling_since = record.get("cooling_since")
            memory.superseded_by_event_id = (
                str(record["superseded_by_event_id"])
                if record.get("superseded_by_event_id")
                else None
            )
            snapshot = record.get("last_cluster_snapshot")
            memory.last_cluster_snapshot_json = snapshot if isinstance(snapshot, dict) else {}
            memory.note = str(record["note"]) if record.get("note") else None
            memory.updated_at = now

            session.add(memory)
            stored.append(memory)

        session.flush()
        for memory in stored:
            session.refresh(memory)
        return stored
