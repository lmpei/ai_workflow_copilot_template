from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.database import session_scope
from app.models.job_hiring_packet import JobHiringPacket
from app.models.job_hiring_packet_event import JobHiringPacketEvent
from app.models.workspace_member import WorkspaceMember


def get_job_hiring_packet(packet_id: str) -> JobHiringPacket | None:
    with session_scope() as session:
        return session.get(JobHiringPacket, packet_id)


def get_job_hiring_packet_for_user(packet_id: str, user_id: str) -> JobHiringPacket | None:
    with session_scope() as session:
        statement = (
            select(JobHiringPacket)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == JobHiringPacket.workspace_id)
            .where(
                JobHiringPacket.id == packet_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return session.scalar(statement)


def list_workspace_job_hiring_packets(workspace_id: str, user_id: str) -> list[JobHiringPacket]:
    with session_scope() as session:
        statement = (
            select(JobHiringPacket)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == JobHiringPacket.workspace_id)
            .where(
                JobHiringPacket.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .order_by(JobHiringPacket.updated_at.desc(), JobHiringPacket.created_at.desc())
        )
        return list(session.scalars(statement))


def get_workspace_job_hiring_packet_by_role_key(
    workspace_id: str,
    target_role_key: str,
) -> JobHiringPacket | None:
    with session_scope() as session:
        statement = (
            select(JobHiringPacket)
            .where(
                JobHiringPacket.workspace_id == workspace_id,
                JobHiringPacket.target_role_key == target_role_key,
            )
            .order_by(JobHiringPacket.updated_at.desc(), JobHiringPacket.created_at.desc())
        )
        return session.scalar(statement)


def list_job_hiring_packet_events(packet_id: str) -> list[JobHiringPacketEvent]:
    with session_scope() as session:
        statement = (
            select(JobHiringPacketEvent)
            .where(JobHiringPacketEvent.job_hiring_packet_id == packet_id)
            .order_by(JobHiringPacketEvent.created_at.desc())
        )
        return list(session.scalars(statement))


def get_job_hiring_packet_event_by_task_id(task_id: str) -> JobHiringPacketEvent | None:
    with session_scope() as session:
        statement = select(JobHiringPacketEvent).where(JobHiringPacketEvent.task_id == task_id)
        return session.scalar(statement)


def create_job_hiring_packet(
    *,
    workspace_id: str,
    created_by: str,
    title: str,
    status: str,
    target_role: str | None,
    target_role_key: str | None,
    seniority: str | None,
    latest_task_id: str,
    latest_task_type: str,
    latest_input_json: dict[str, object],
    latest_result_json: dict[str, object],
    latest_summary: str,
    latest_recommended_outcome: str | None,
    latest_evidence_status: str | None,
    latest_fit_signal: str | None,
    latest_shortlist_json: dict[str, object] | None,
    latest_next_steps_json: list[str],
    candidate_labels_json: list[str],
    comparison_history_count: int,
) -> JobHiringPacket:
    now = datetime.now(UTC)
    packet = JobHiringPacket(
        id=str(uuid4()),
        workspace_id=workspace_id,
        created_by=created_by,
        title=title,
        status=status,
        target_role=target_role,
        target_role_key=target_role_key,
        seniority=seniority,
        latest_task_id=latest_task_id,
        latest_task_type=latest_task_type,
        latest_input_json=latest_input_json,
        latest_result_json=latest_result_json,
        latest_summary=latest_summary,
        latest_recommended_outcome=latest_recommended_outcome,
        latest_evidence_status=latest_evidence_status,
        latest_fit_signal=latest_fit_signal,
        latest_shortlist_json=latest_shortlist_json,
        latest_next_steps_json=latest_next_steps_json,
        candidate_labels_json=candidate_labels_json,
        comparison_history_count=comparison_history_count,
        event_count=1,
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(packet)
        session.flush()
        session.refresh(packet)
        return packet


def create_job_hiring_packet_event(
    *,
    job_hiring_packet_id: str,
    task_id: str,
    task_type: str,
    event_kind: str,
    title: str,
    summary: str,
    packet_status: str,
    candidate_label: str | None,
    target_role: str | None,
    fit_signal: str | None,
    evidence_status: str | None,
    recommended_outcome: str | None,
    comparison_task_ids_json: list[str],
    shortlist_entry_count: int,
    created_at: datetime,
) -> JobHiringPacketEvent:
    event = JobHiringPacketEvent(
        id=str(uuid4()),
        job_hiring_packet_id=job_hiring_packet_id,
        task_id=task_id,
        task_type=task_type,
        event_kind=event_kind,
        title=title,
        summary=summary,
        packet_status=packet_status,
        candidate_label=candidate_label,
        target_role=target_role,
        fit_signal=fit_signal,
        evidence_status=evidence_status,
        recommended_outcome=recommended_outcome,
        comparison_task_ids_json=comparison_task_ids_json,
        shortlist_entry_count=shortlist_entry_count,
        created_at=created_at,
    )
    with session_scope() as session:
        session.add(event)
        session.flush()
        session.refresh(event)
        return event


def update_job_hiring_packet_snapshot(
    packet_id: str,
    *,
    title: str | None = None,
    status: str | None = None,
    target_role: str | None = None,
    target_role_key: str | None = None,
    seniority: str | None = None,
    latest_task_id: str | None = None,
    latest_task_type: str | None = None,
    latest_input_json: dict[str, object] | None = None,
    latest_result_json: dict[str, object] | None = None,
    latest_summary: str | None = None,
    latest_recommended_outcome: str | None = None,
    latest_evidence_status: str | None = None,
    latest_fit_signal: str | None = None,
    latest_shortlist_json: dict[str, object] | None = None,
    latest_next_steps_json: list[str] | None = None,
    candidate_labels_json: list[str] | None = None,
    comparison_history_count: int | None = None,
    event_count: int | None = None,
) -> JobHiringPacket | None:
    with session_scope() as session:
        packet = session.get(JobHiringPacket, packet_id)
        if packet is None:
            return None

        if title is not None:
            packet.title = title
        if status is not None:
            packet.status = status
        packet.target_role = target_role
        packet.target_role_key = target_role_key
        packet.seniority = seniority
        if latest_task_id is not None:
            packet.latest_task_id = latest_task_id
        if latest_task_type is not None:
            packet.latest_task_type = latest_task_type
        if latest_input_json is not None:
            packet.latest_input_json = latest_input_json
        if latest_result_json is not None:
            packet.latest_result_json = latest_result_json
        if latest_summary is not None:
            packet.latest_summary = latest_summary
        packet.latest_recommended_outcome = latest_recommended_outcome
        packet.latest_evidence_status = latest_evidence_status
        packet.latest_fit_signal = latest_fit_signal
        packet.latest_shortlist_json = latest_shortlist_json
        if latest_next_steps_json is not None:
            packet.latest_next_steps_json = latest_next_steps_json
        if candidate_labels_json is not None:
            packet.candidate_labels_json = candidate_labels_json
        if comparison_history_count is not None:
            packet.comparison_history_count = comparison_history_count
        if event_count is not None:
            packet.event_count = event_count
        packet.updated_at = datetime.now(UTC)

        session.add(packet)
        session.flush()
        session.refresh(packet)
        return packet
