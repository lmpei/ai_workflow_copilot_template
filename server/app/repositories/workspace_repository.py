from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import delete, select, update

from app.core.database import session_scope
from app.models.agent_run import AgentRun
from app.models.ai_frontier_research_record import AiFrontierResearchRecord
from app.models.ai_hot_tracker_tracking_run import AiHotTrackerTrackingRun
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.embedding import Embedding
from app.models.eval_case import EvalCase
from app.models.eval_dataset import EvalDataset
from app.models.eval_result import EvalResult
from app.models.eval_run import EvalRun
from app.models.job_hiring_packet import JobHiringPacket
from app.models.job_hiring_packet_event import JobHiringPacketEvent
from app.models.message import Message
from app.models.research_analysis_run import ResearchAnalysisRun
from app.models.research_asset import ResearchAsset
from app.models.research_asset_revision import ResearchAssetRevision
from app.models.research_external_resource_snapshot import ResearchExternalResourceSnapshot
from app.models.support_case import SupportCase
from app.models.support_case_event import SupportCaseEvent
from app.models.task import Task
from app.models.tool_call import ToolCall
from app.models.trace import Trace
from app.models.workspace import Workspace
from app.models.workspace_connector_consent import WorkspaceConnectorConsent
from app.models.workspace_member import WorkspaceMember
from app.schemas.scenario import merge_module_config
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


@dataclass(slots=True)
class WorkspaceDeleteArtifacts:
    file_paths: list[str]
    vector_ids: list[str]


def list_workspaces(user_id: str) -> list[Workspace]:
    with session_scope() as session:
        statement = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.created_at.asc())
        )
        result = session.scalars(statement)
        return list(result)


def get_workspace(workspace_id: str, user_id: str) -> Workspace | None:
    with session_scope() as session:
        statement = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                Workspace.id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return session.scalar(statement)


def create_workspace(payload: WorkspaceCreate, owner_id: str) -> Workspace:
    now = datetime.now(UTC)
    module_type = payload.module_type
    module_config_json = merge_module_config(module_type, payload.module_config_json)
    workspace = Workspace(
        id=str(uuid4()),
        owner_id=owner_id,
        name=payload.name,
        type=module_type,
        module_type=module_type,
        description=payload.description,
        module_config_json=module_config_json,
        created_at=now,
        updated_at=now,
    )
    membership = WorkspaceMember(
        id=str(uuid4()),
        workspace_id=workspace.id,
        user_id=owner_id,
        member_role="owner",
        created_at=now,
    )
    with session_scope() as session:
        session.add(workspace)
        session.add(membership)
        session.flush()
        session.refresh(workspace)
        return workspace


def update_workspace(workspace_id: str, user_id: str, payload: WorkspaceUpdate) -> Workspace | None:
    with session_scope() as session:
        statement = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                Workspace.id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        workspace = session.scalar(statement)
        if workspace is None:
            return None

        has_module_contract_update = any(
            value is not None
            for value in (
                payload.module_type,
                payload.module_config_json,
            )
        )

        changed = False
        if payload.name is not None:
            workspace.name = payload.name
            changed = True
        if has_module_contract_update:
            next_module_type = payload.module_type or workspace.module_type
            next_module_config_json = merge_module_config(
                next_module_type,
                payload.module_config_json if payload.module_config_json is not None else workspace.module_config_json,
            )
            if (
                workspace.type != next_module_type
                or workspace.module_type != next_module_type
                or workspace.module_config_json != next_module_config_json
            ):
                workspace.type = next_module_type
                workspace.module_type = next_module_type
                workspace.module_config_json = next_module_config_json
                changed = True
        if payload.description is not None:
            workspace.description = payload.description
            changed = True
        if changed:
            workspace.updated_at = datetime.now(UTC)

        session.add(workspace)
        session.flush()
        session.refresh(workspace)
        return workspace


def _list_scalars(session, statement) -> list[str]:
    return list(session.scalars(statement))


def delete_workspace_tree(workspace_id: str, user_id: str) -> WorkspaceDeleteArtifacts | None:
    with session_scope() as session:
        statement = select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.owner_id == user_id,
        )
        workspace = session.scalar(statement)
        if workspace is None:
            return None

        conversation_ids = _list_scalars(
            session,
            select(Conversation.id).where(Conversation.workspace_id == workspace_id),
        )
        document_ids = _list_scalars(
            session,
            select(Document.id).where(Document.workspace_id == workspace_id),
        )
        task_ids = _list_scalars(
            session,
            select(Task.id).where(Task.workspace_id == workspace_id),
        )
        run_ids = _list_scalars(
            session,
            select(ResearchAnalysisRun.id).where(ResearchAnalysisRun.workspace_id == workspace_id),
        )
        hot_tracker_run_ids = _list_scalars(
            session,
            select(AiHotTrackerTrackingRun.id).where(AiHotTrackerTrackingRun.workspace_id == workspace_id),
        )
        snapshot_ids = _list_scalars(
            session,
            select(ResearchExternalResourceSnapshot.id).where(
                ResearchExternalResourceSnapshot.workspace_id == workspace_id
            ),
        )
        dataset_ids = _list_scalars(
            session,
            select(EvalDataset.id).where(EvalDataset.workspace_id == workspace_id),
        )
        eval_run_ids = _list_scalars(
            session,
            select(EvalRun.id).where(EvalRun.workspace_id == workspace_id),
        )
        eval_case_ids = _list_scalars(
            session,
            select(EvalCase.id).where(EvalCase.dataset_id.in_(dataset_ids))
            if dataset_ids
            else select(EvalCase.id).where(EvalCase.id == "__never__"),
        )
        asset_ids = _list_scalars(
            session,
            select(ResearchAsset.id).where(ResearchAsset.workspace_id == workspace_id),
        )
        support_case_ids = _list_scalars(
            session,
            select(SupportCase.id).where(SupportCase.workspace_id == workspace_id),
        )
        hiring_packet_ids = _list_scalars(
            session,
            select(JobHiringPacket.id).where(JobHiringPacket.workspace_id == workspace_id),
        )
        agent_run_ids = _list_scalars(
            session,
            select(AgentRun.id).where(AgentRun.task_id.in_(task_ids))
            if task_ids
            else select(AgentRun.id).where(AgentRun.id == "__never__"),
        )
        file_paths = [
            file_path
            for file_path in _list_scalars(
                session,
                select(Document.file_path).where(Document.workspace_id == workspace_id),
            )
            if file_path
        ]
        vector_ids = [
            vector_store_id
            for vector_store_id in _list_scalars(
                session,
                (
                    select(Embedding.vector_store_id)
                    .join(DocumentChunk, Embedding.document_chunk_id == DocumentChunk.id)
                    .join(Document, DocumentChunk.document_id == Document.id)
                    .where(Document.workspace_id == workspace_id)
                ),
            )
            if vector_store_id
        ]

        if snapshot_ids:
            session.execute(
                update(ResearchAnalysisRun)
                .where(ResearchAnalysisRun.selected_external_resource_snapshot_id.in_(snapshot_ids))
                .values(selected_external_resource_snapshot_id=None)
            )
            session.execute(
                update(ResearchAnalysisRun)
                .where(ResearchAnalysisRun.external_resource_snapshot_id.in_(snapshot_ids))
                .values(external_resource_snapshot_id=None)
            )

        if run_ids:
            session.execute(
                update(ResearchAnalysisRun)
                .where(ResearchAnalysisRun.resumed_from_run_id.in_(run_ids))
                .values(resumed_from_run_id=None)
            )
            session.execute(
                update(ResearchExternalResourceSnapshot)
                .where(ResearchExternalResourceSnapshot.source_run_id.in_(run_ids))
                .values(source_run_id=None)
            )
            session.execute(
                update(AiFrontierResearchRecord)
                .where(AiFrontierResearchRecord.source_run_id.in_(run_ids))
                .values(source_run_id=None)
            )

        if hot_tracker_run_ids:
            session.execute(
                update(AiHotTrackerTrackingRun)
                .where(AiHotTrackerTrackingRun.previous_run_id.in_(hot_tracker_run_ids))
                .values(previous_run_id=None)
            )

        session.execute(delete(AiFrontierResearchRecord).where(AiFrontierResearchRecord.workspace_id == workspace_id))
        session.execute(
            delete(AiHotTrackerTrackingRun).where(AiHotTrackerTrackingRun.workspace_id == workspace_id)
        )
        session.execute(
            delete(ResearchExternalResourceSnapshot).where(
                ResearchExternalResourceSnapshot.workspace_id == workspace_id
            )
        )
        session.execute(
            delete(ResearchAnalysisRun).where(ResearchAnalysisRun.workspace_id == workspace_id)
        )
        session.execute(delete(Trace).where(Trace.workspace_id == workspace_id))

        if eval_run_ids:
            session.execute(delete(EvalResult).where(EvalResult.eval_run_id.in_(eval_run_ids)))
        if eval_case_ids:
            session.execute(delete(EvalResult).where(EvalResult.eval_case_id.in_(eval_case_ids)))
            session.execute(delete(EvalCase).where(EvalCase.id.in_(eval_case_ids)))
        if eval_run_ids:
            session.execute(delete(EvalRun).where(EvalRun.id.in_(eval_run_ids)))
        if dataset_ids:
            session.execute(delete(EvalDataset).where(EvalDataset.id.in_(dataset_ids)))

        if agent_run_ids:
            session.execute(delete(ToolCall).where(ToolCall.agent_run_id.in_(agent_run_ids)))
            session.execute(delete(AgentRun).where(AgentRun.id.in_(agent_run_ids)))

        if asset_ids:
            session.execute(
                delete(ResearchAssetRevision).where(
                    ResearchAssetRevision.research_asset_id.in_(asset_ids)
                )
            )
            session.execute(delete(ResearchAsset).where(ResearchAsset.id.in_(asset_ids)))

        if support_case_ids:
            session.execute(
                delete(SupportCaseEvent).where(SupportCaseEvent.support_case_id.in_(support_case_ids))
            )
            session.execute(delete(SupportCase).where(SupportCase.id.in_(support_case_ids)))

        if hiring_packet_ids:
            session.execute(
                delete(JobHiringPacketEvent).where(
                    JobHiringPacketEvent.job_hiring_packet_id.in_(hiring_packet_ids)
                )
            )
            session.execute(delete(JobHiringPacket).where(JobHiringPacket.id.in_(hiring_packet_ids)))

        session.execute(
            delete(WorkspaceConnectorConsent).where(
                WorkspaceConnectorConsent.workspace_id == workspace_id
            )
        )

        if document_ids:
            session.execute(
                delete(Embedding).where(
                    Embedding.document_chunk_id.in_(
                        select(DocumentChunk.id).where(DocumentChunk.document_id.in_(document_ids))
                    )
                )
            )
            session.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id.in_(document_ids))
            )
            session.execute(delete(Document).where(Document.id.in_(document_ids)))

        if conversation_ids:
            session.execute(delete(Message).where(Message.conversation_id.in_(conversation_ids)))
            session.execute(delete(Conversation).where(Conversation.id.in_(conversation_ids)))

        if task_ids:
            session.execute(delete(Task).where(Task.id.in_(task_ids)))

        session.execute(delete(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id))
        session.delete(workspace)

        return WorkspaceDeleteArtifacts(
            file_paths=file_paths,
            vector_ids=vector_ids,
        )
