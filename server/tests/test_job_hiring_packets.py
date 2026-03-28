from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import reset_database_for_tests
from app.models.document import DOCUMENT_STATUS_INDEXED
from app.repositories import document_repository, task_repository
from app.repositories.user_repository import create_user
from app.repositories.workspace_repository import create_workspace
from app.schemas.workspace import WorkspaceCreate
from app.services import job_hiring_packet_service, task_execution_service
from app.services.retrieval_service import RetrievedChunk


@pytest.fixture(autouse=True)
def reset_database() -> None:
    reset_database_for_tests()


def _register_and_login(client: TestClient, *, email: str, name: str) -> dict[str, str]:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "super-secret",
            "name": name,
        },
    )
    assert register_response.status_code == 201
    user = register_response.json()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "super-secret",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {
        "user_id": user["id"],
        "token": token,
    }


def _create_workspace(
    client: TestClient,
    token: str,
    *,
    name: str = "Job Demo",
    module_type: str = "job",
) -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"name": name, "module_type": module_type},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_completed_job_task(
    *,
    workspace_id: str,
    user_id: str,
    task_type: str = "resume_match",
    input_json: dict[str, object] | None = None,
    result_json: dict[str, object] | None = None,
) -> str:
    task = task_repository.create_task(
        workspace_id=workspace_id,
        task_type=task_type,
        created_by=user_id,
        input_json=input_json
        or {
            "target_role": "Platform engineer",
            "candidate_label": "Candidate A",
            "seniority": "senior",
            "must_have_skills": ["Python", "API design"],
        },
    )
    running_task = task_repository.update_task_status(task.id, next_status="running")
    assert running_task is not None
    completed_task = task_repository.update_task_status(
        task.id,
        next_status="done",
        output_json={
            "result": result_json
            or {
                "module_type": "job",
                "task_type": task_type,
                "title": "Structured Resume Match Review",
                "summary": "Candidate A shows grounded backend ownership for the platform role.",
                "input": {
                    "target_role": "Platform engineer",
                    "candidate_label": "Candidate A",
                    "seniority": "senior",
                    "must_have_skills": ["Python", "API design"],
                    "preferred_skills": ["Distributed systems"],
                    "comparison_task_ids": [],
                },
                "review_brief": {
                    "role_summary": "Platform engineer",
                    "candidate_label": "Candidate A",
                    "seniority": "senior",
                    "must_have_skills": ["Python", "API design"],
                    "preferred_skills": ["Distributed systems"],
                    "evidence_status": "grounded_matches",
                    "comparison_task_count": 0,
                },
                "findings": [
                    {
                        "title": "Grounded backend signal",
                        "summary": "Candidate A has strong backend ownership grounded in indexed resume evidence.",
                        "evidence_ref_ids": ["chunk-1"],
                    }
                ],
                "gaps": [],
                "assessment": {
                    "fit_signal": "grounded_match_found",
                    "evidence_status": "grounded_matches",
                    "recommended_outcome": "advance_to_manual_review",
                    "confidence_note": "Grounded evidence exists in the indexed hiring materials.",
                    "rationale": "The indexed materials support a deeper reviewer conversation.",
                },
                "comparison_candidates": [],
                "open_questions": ["Should the candidate lead the API reliability area?"],
                "next_steps": ["Review grounded evidence before the hiring discussion."],
                "highlights": ["Candidate A has strong backend ownership"],
                "evidence": [],
                "artifacts": {
                    "document_count": 1,
                    "match_count": 1,
                    "documents": [],
                    "matches": [],
                    "tool_call_ids": [],
                    "evidence_status": "grounded_matches",
                    "fit_signal": "grounded_match_found",
                    "recommended_next_step": "Advance to manual review.",
                },
                "metadata": {},
            }
        },
    )
    assert completed_task is not None
    return task.id


def test_run_task_execution_syncs_job_hiring_packet_metadata_and_creates_packet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert "Platform engineer" in question
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="candidate-a.md",
                    chunk_index=0,
                    snippet="Candidate A led backend ownership for a platform migration.",
                    content="Candidate A led backend ownership for a platform migration.",
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    unique_suffix = uuid4().hex
    user = create_user(
        email=f"job-packet-exec-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Job Packet Exec",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Job Packet Workspace", module_type="job"),
        owner_id=user.id,
    )
    document_repository.create_document(
        document_id=str(uuid4()),
        workspace_id=workspace.id,
        title="candidate-a.md",
        file_path="uploads/candidate-a.md",
        mime_type="text/markdown",
        created_by=user.id,
        status=DOCUMENT_STATUS_INDEXED,
    )
    task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type="resume_match",
        created_by=user.id,
        input_json={
            "target_role": "Platform engineer",
            "candidate_label": "Candidate A",
            "seniority": "senior",
            "must_have_skills": ["Python", "API design"],
        },
    )

    output = task_execution_service.run_task_execution(task.id)
    persisted_task = task_repository.get_task(task.id)
    assert persisted_task is not None

    packet_link = output["result"]["metadata"]["job_hiring_packet"]
    assert isinstance(packet_link, dict)
    assert packet_link["packet_status"] == "review_ready"

    packets = job_hiring_packet_service.list_workspace_job_hiring_packets(
        workspace_id=workspace.id,
        user_id=user.id,
    )
    assert len(packets) == 1
    assert packets[0].id == packet_link["packet_id"]
    assert packets[0].latest_candidate_labels == ["Candidate A"]
    assert packets[0].comparison_history_count == 0
    assert packets[0].action_loop.suggested_task_type == "resume_match"
    assert packets[0].action_loop.comparison_mode is False
    assert packets[0].latest_packet_note == "The workspace contains direct grounded evidence that should be reviewed before deciding the next hiring step."

    packet = job_hiring_packet_service.get_job_hiring_packet(
        packet_id=packets[0].id,
        user_id=user.id,
    )
    assert packet is not None
    assert len(packet.events) == 1
    assert packet.events[0].task_id == task.id
    assert packet.events[0].event_kind == "candidate_review"
    assert packet.action_loop.suggested_task_type == "resume_match"
    assert packet.action_loop.comparison_mode is False
    assert persisted_task.output_json["result"]["metadata"]["job_hiring_packet"]["packet_id"] == packet.id


def test_job_hiring_packet_routes_list_and_get_shortlist_history(client: TestClient) -> None:
    auth = _register_and_login(client, email="job-packet-owner@example.com", name="Job Packet Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], module_type="job")

    candidate_a_task_id = _create_completed_job_task(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
    )
    candidate_a_task = task_repository.get_task(candidate_a_task_id)
    assert candidate_a_task is not None
    candidate_a_result = candidate_a_task.output_json["result"]
    job_hiring_packet_service.sync_job_hiring_packet_from_task(task=candidate_a_task, result_json=candidate_a_result)

    candidate_b_task_id = _create_completed_job_task(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        input_json={
            "target_role": "Platform engineer",
            "candidate_label": "Candidate B",
            "seniority": "senior",
            "must_have_skills": ["Python", "API design"],
        },
        result_json={
            "module_type": "job",
            "task_type": "resume_match",
            "title": "Structured Resume Match Review",
            "summary": "Candidate B still lacks strong grounded materials for a confident shortlist decision.",
            "input": {
                "target_role": "Platform engineer",
                "candidate_label": "Candidate B",
                "seniority": "senior",
                "must_have_skills": ["Python", "API design"],
                "comparison_task_ids": [],
            },
            "review_brief": {
                "role_summary": "Platform engineer",
                "candidate_label": "Candidate B",
                "seniority": "senior",
                "must_have_skills": ["Python", "API design"],
                "preferred_skills": [],
                "evidence_status": "documents_only",
                "comparison_task_count": 0,
            },
            "findings": [],
            "gaps": ["Indexed materials are still too thin for a confident grounded review."],
            "assessment": {
                "fit_signal": "insufficient_grounding",
                "evidence_status": "documents_only",
                "recommended_outcome": "collect_more_hiring_signal",
                "confidence_note": "Some materials exist, but they are still thin.",
                "rationale": "The reviewer should gather stronger candidate signal before final ranking.",
            },
            "comparison_candidates": [],
            "open_questions": ["What concrete backend ownership examples can Candidate B provide?"],
            "next_steps": ["Gather stronger candidate evidence before shortlist ranking."],
            "highlights": ["Candidate B still lacks strong grounded materials"],
            "evidence": [],
            "artifacts": {
                "document_count": 1,
                "match_count": 0,
                "documents": [],
                "matches": [],
                "tool_call_ids": [],
                "evidence_status": "documents_only",
                "fit_signal": "insufficient_grounding",
                "recommended_next_step": "Gather stronger candidate evidence.",
            },
            "metadata": {},
        },
    )
    candidate_b_task = task_repository.get_task(candidate_b_task_id)
    assert candidate_b_task is not None
    candidate_b_result = candidate_b_task.output_json["result"]
    metadata = job_hiring_packet_service.sync_job_hiring_packet_from_task(task=candidate_b_task, result_json=candidate_b_result)
    packet_id = metadata["job_hiring_packet"]["packet_id"]

    shortlist_task_id = _create_completed_job_task(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        input_json={
            "target_role": "Platform engineer",
            "comparison_task_ids": [candidate_a_task_id, candidate_b_task_id],
            "comparison_notes": "Prioritize backend ownership and readiness.",
        },
        result_json={
            "module_type": "job",
            "task_type": "resume_match",
            "title": "Candidate Comparison Shortlist",
            "summary": "Compared Candidate A and Candidate B for the Platform engineer shortlist.",
            "input": {
                "target_role": "Platform engineer",
                "comparison_task_ids": [candidate_a_task_id, candidate_b_task_id],
                "comparison_notes": "Prioritize backend ownership and readiness.",
            },
            "review_brief": {
                "role_summary": "Platform engineer",
                "must_have_skills": ["Python", "API design"],
                "preferred_skills": [],
                "evidence_status": "grounded_matches",
                "comparison_task_count": 2,
            },
            "findings": [],
            "gaps": ["Candidate B still lacks enough grounded evidence."],
            "assessment": {
                "fit_signal": "grounded_match_found",
                "evidence_status": "grounded_matches",
                "recommended_outcome": "advance_to_manual_review",
                "confidence_note": "Shortlist comparison has enough grounded signal.",
                "rationale": "Candidate A should be reviewed first, while Candidate B stays provisional.",
            },
            "comparison_candidates": [
                {
                    "task_id": candidate_a_task_id,
                    "task_type": "resume_match",
                    "candidate_label": "Candidate A",
                    "title": "Structured Resume Match Review",
                    "summary": "Candidate A shows grounded backend ownership for the platform role.",
                    "target_role": "Platform engineer",
                    "fit_signal": "grounded_match_found",
                    "evidence_status": "grounded_matches",
                    "recommended_outcome": "advance_to_manual_review",
                    "findings": [],
                    "highlights": ["Grounded backend ownership"],
                    "evidence_ref_ids": ["chunk-1"],
                },
                {
                    "task_id": candidate_b_task_id,
                    "task_type": "resume_match",
                    "candidate_label": "Candidate B",
                    "title": "Structured Resume Match Review",
                    "summary": "Candidate B still lacks strong grounded materials for a confident shortlist decision.",
                    "target_role": "Platform engineer",
                    "fit_signal": "insufficient_grounding",
                    "evidence_status": "documents_only",
                    "recommended_outcome": "collect_more_hiring_signal",
                    "findings": [],
                    "highlights": ["Grounding still thin"],
                    "evidence_ref_ids": [],
                },
            ],
            "shortlist": {
                "comparison_task_ids": [candidate_a_task_id, candidate_b_task_id],
                "comparison_notes": "Prioritize backend ownership and readiness.",
                "shortlist_summary": "Compared 2 completed candidate review tasks for Platform engineer.",
                "entries": [
                    {
                        "rank": 1,
                        "task_id": candidate_a_task_id,
                        "candidate_label": "Candidate A",
                        "fit_signal": "grounded_match_found",
                        "evidence_status": "grounded_matches",
                        "recommendation": "Prioritize for shortlist discussion",
                        "rationale": "Grounded backend signal is already strong.",
                        "risks": [],
                        "interview_focus": ["Validate backend ownership depth."],
                        "evidence_ref_ids": ["chunk-1"],
                    },
                    {
                        "rank": 2,
                        "task_id": candidate_b_task_id,
                        "candidate_label": "Candidate B",
                        "fit_signal": "insufficient_grounding",
                        "evidence_status": "documents_only",
                        "recommendation": "Keep in consideration but gather more signal",
                        "rationale": "Grounding is still too thin for a final shortlist position.",
                        "risks": ["Grounding is incomplete for this candidate review."],
                        "interview_focus": ["Probe concrete backend ownership examples."],
                        "evidence_ref_ids": [],
                    },
                ],
                "risks": ["Candidate B still lacks enough grounded evidence."],
                "interview_focus": ["Validate backend ownership depth."],
                "gaps": ["Candidate B still lacks enough grounded evidence."],
            },
            "open_questions": ["Should Candidate B be revisited after stronger evidence is added?"],
            "next_steps": ["Review Candidate A first and gather more signal for Candidate B."],
            "highlights": ["Candidate A leads the current shortlist"],
            "evidence": [],
            "artifacts": {
                "document_count": 1,
                "match_count": 1,
                "documents": [],
                "matches": [],
                "tool_call_ids": [],
                "evidence_status": "grounded_matches",
                "fit_signal": "grounded_match_found",
                "recommended_next_step": "Review Candidate A first and gather more signal for Candidate B.",
            },
            "metadata": {},
        },
    )
    shortlist_task = task_repository.get_task(shortlist_task_id)
    assert shortlist_task is not None
    shortlist_result = shortlist_task.output_json["result"]
    job_hiring_packet_service.sync_job_hiring_packet_from_task(task=shortlist_task, result_json=shortlist_result)

    list_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/job-hiring-packets",
        headers=headers,
    )
    assert list_response.status_code == 200
    listed_packets = list_response.json()
    assert len(listed_packets) == 1
    assert listed_packets[0]["id"] == packet_id
    assert listed_packets[0]["comparison_history_count"] == 1
    assert listed_packets[0]["latest_candidate_labels"] == ["Candidate A", "Candidate B"]
    assert listed_packets[0]["action_loop"]["suggested_task_type"] == "resume_match"
    assert listed_packets[0]["action_loop"]["comparison_mode"] is True
    assert listed_packets[0]["latest_packet_note"] == "Prioritize backend ownership and readiness."

    detail_response = client.get(f"/api/v1/job-hiring-packets/{packet_id}", headers=headers)
    assert detail_response.status_code == 200
    packet = detail_response.json()
    assert packet["id"] == packet_id
    assert packet["status"] == "shortlist_ready"
    assert packet["action_loop"]["comparison_mode"] is True
    assert packet["latest_shortlist"]["entries"][0]["candidate_label"] == "Candidate A"
    assert packet["latest_shortlist"]["entries"][1]["candidate_label"] == "Candidate B"
    assert len(packet["events"]) == 3
    assert packet["events"][0]["task_id"] == shortlist_task_id
    assert packet["events"][0]["event_kind"] == "shortlist_refresh"
