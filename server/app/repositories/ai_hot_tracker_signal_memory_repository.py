import hashlib
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import session_scope
from app.models.ai_hot_tracker_signal_memory import AiHotTrackerSignalMemory


def _build_signal_memory_storage_id(*, workspace_id: str, event_id: str) -> str:
    digest = hashlib.sha1(f"{workspace_id}:{event_id}".encode("utf-8")).hexdigest()
    return f"memory-{digest[:12]}"


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
    normalized_records: list[tuple[dict[str, object], str, str]] = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("event_id"), str):
            continue
        event_id = str(record["event_id"])
        fingerprint = str(record.get("fingerprint") or event_id)
        normalized_records.append((record, event_id, fingerprint))

    if not normalized_records:
        return []

    event_ids = [event_id for _, event_id, _ in normalized_records]
    fingerprints = [fingerprint for _, _, fingerprint in normalized_records]

    with session_scope() as session:
        existing_by_id = {
            item.id: item
            for item in session.scalars(
                select(AiHotTrackerSignalMemory).where(
                    AiHotTrackerSignalMemory.workspace_id == workspace_id,
                    AiHotTrackerSignalMemory.id.in_(event_ids),
                )
            ).all()
        }
        existing_by_fingerprint = {
            item.fingerprint: item
            for item in session.scalars(
                select(AiHotTrackerSignalMemory).where(
                    AiHotTrackerSignalMemory.workspace_id == workspace_id,
                    AiHotTrackerSignalMemory.fingerprint.in_(fingerprints),
                )
            ).all()
        }

        stored: list[AiHotTrackerSignalMemory] = []
        for record, event_id, fingerprint in normalized_records:
            memory = existing_by_fingerprint.get(fingerprint) or existing_by_id.get(event_id)
            if memory is None:
                memory = AiHotTrackerSignalMemory(
                    id=_build_signal_memory_storage_id(
                        workspace_id=workspace_id,
                        event_id=event_id,
                    ),
                    workspace_id=workspace_id,
                    created_at=now,
                )

            memory.fingerprint = fingerprint
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
            if "event_id" not in memory.last_cluster_snapshot_json:
                memory.last_cluster_snapshot_json = {
                    **memory.last_cluster_snapshot_json,
                    "event_id": event_id,
                }
            memory.note = str(record["note"]) if record.get("note") else None
            memory.updated_at = now

            session.add(memory)
            existing_by_fingerprint[fingerprint] = memory
            existing_by_id[event_id] = memory
            stored.append(memory)

        session.flush()
        for memory in stored:
            session.refresh(memory)
        return stored
