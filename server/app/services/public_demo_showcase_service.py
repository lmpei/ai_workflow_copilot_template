from dataclasses import dataclass, field

from app.core.config import get_settings
from app.schemas.public_demo import (
    PublicDemoSeedDocumentResponse,
    PublicDemoShowcaseStepResponse,
    PublicDemoTemplateResponse,
    PublicDemoWorkspaceSeedResponse,
)
from app.schemas.scenario import ModuleType, ScenarioTaskType
from app.schemas.workspace import WorkspaceCreate
from app.services import document_service, workspace_service
from app.services.public_demo_service import PublicDemoLimitError


@dataclass(frozen=True, slots=True)
class DemoSeedDocument:
    title: str
    summary: str
    body: str


@dataclass(frozen=True, slots=True)
class DemoShowcaseStep:
    title: str
    description: str
    route_suffix: str
    cta_label: str
    sample_prompt: str | None = None
    sample_task_type: ScenarioTaskType | None = None
    sample_task_input: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DemoTemplate:
    template_id: str
    module_type: ModuleType
    title: str
    summary: str
    workspace_name: str
    workspace_description: str
    seeded_documents: tuple[DemoSeedDocument, ...]
    showcase_steps: tuple[DemoShowcaseStep, ...]


_DEMO_TEMPLATES: dict[str, DemoTemplate] = {
    "research": DemoTemplate(
        template_id="research",
        module_type="research",
        title="Research Briefing Demo",
        summary="Create a grounded research workspace with seeded launch materials, then turn the corpus into a concise brief.",
        workspace_name="Guided Demo - Research Briefing",
        workspace_description="Seeded research workspace for the public demo path.",
        seeded_documents=(
            DemoSeedDocument(
                title="launch-memo.txt",
                summary="Internal product memo describing the pilot goal, scope, and launch risks.",
                body=(
                    "Acme Team Inbox Pilot Launch Memo\n"
                    "\n"
                    "Goal: launch a shared team inbox pilot for small support teams in Q3.\n"
                    "Primary value: reduce response time for high-volume support queues.\n"
                    "Known risks: onboarding complexity, unclear routing ownership, and limited analytics coverage.\n"
                    "Success measures: first-response time under 20 minutes and a 25 percent drop in backlog volume.\n"
                    "Open concern: the current routing logic does not explain why tickets move between teammates.\n"
                ),
            ),
            DemoSeedDocument(
                title="customer-interviews.txt",
                summary="Condensed interview notes from pilot customers describing friction and desired outcomes.",
                body=(
                    "Pilot Customer Interview Notes\n"
                    "\n"
                    "Customer A wants routing explanations because managers need to audit ticket handoffs.\n"
                    "Customer B says setup is confusing when more than one inbox rule applies to the same case.\n"
                    "Customer C values SLA visibility and wants clearer reporting on overdue conversations.\n"
                    "All three customers say rollout will stall if admins cannot explain ownership changes quickly.\n"
                ),
            ),
            DemoSeedDocument(
                title="competitor-watch.txt",
                summary="Brief market scan covering competitor strengths and gaps in shared inbox tooling.",
                body=(
                    "Competitor Watch\n"
                    "\n"
                    "Vendor Northstar emphasizes audit logs and approval-friendly routing changes.\n"
                    "Vendor Relay differentiates on analytics dashboards for backlog, SLA breaches, and handoff reasons.\n"
                    "Neither competitor is especially strong in setup simplicity, but both communicate routing visibility clearly.\n"
                ),
            ),
        ),
        showcase_steps=(
            DemoShowcaseStep(
                title="Review the seeded corpus",
                description="Open the documents surface and confirm the demo workspace already has indexed source material.",
                route_suffix="/documents",
                cta_label="Open documents",
            ),
            DemoShowcaseStep(
                title="Ask a grounded question",
                description="Use chat to verify that answers cite the seeded launch material instead of free-writing from memory.",
                route_suffix="/chat",
                cta_label="Open chat",
                sample_prompt="What are the strongest launch risks for the team inbox pilot, and which documents support them?",
            ),
            DemoShowcaseStep(
                title="Run a research task",
                description="Launch a structured research summary to turn the same corpus into an evidence-backed briefing.",
                route_suffix="/tasks",
                cta_label="Open tasks",
                sample_task_type="research_summary",
                sample_task_input={
                    "goal": "Summarize the strongest evidence about pilot launch risk and recommend next steps for the launch review.",
                    "focus_areas": ["launch risk", "routing visibility", "analytics readiness"],
                    "key_questions": [
                        "What could block rollout confidence?",
                        "Which evidence points to the biggest operational gap?",
                    ],
                    "requested_sections": ["summary", "findings", "evidence", "next_steps"],
                    "deliverable": "brief",
                },
            ),
        ),
    ),
    "support": DemoTemplate(
        template_id="support",
        module_type="support",
        title="Support Escalation Demo",
        summary="Seed a support knowledge base, then walk from frontline triage to a grounded escalation packet.",
        workspace_name="Guided Demo - Support Escalation",
        workspace_description="Seeded support workspace for the public demo path.",
        seeded_documents=(
            DemoSeedDocument(
                title="password-reset-kb.txt",
                summary="Knowledge-base guidance for reset links, account ownership checks, and safe reissue rules.",
                body=(
                    "Password Reset Knowledge Base\n"
                    "\n"
                    "Reset links expire after 30 minutes.\n"
                    "Frontline support may reissue a reset link after confirming account ownership with the last successful login timestamp or billing ZIP code.\n"
                    "If the same user reports repeated expiry within one hour, escalate to identity engineering because email redirect mismatches may be involved.\n"
                ),
            ),
            DemoSeedDocument(
                title="incident-update.txt",
                summary="Incident update describing intermittent expiry behavior after a token-validation rollout.",
                body=(
                    "Incident Update - Identity Token Validation\n"
                    "\n"
                    "A rollout on Tuesday introduced intermittent false expiry responses for reset links opened in mobile email clients.\n"
                    "Scope is limited but unresolved.\n"
                    "Temporary mitigation: advise users to request a fresh link and open it in the system browser.\n"
                ),
            ),
            DemoSeedDocument(
                title="escalation-runbook.txt",
                summary="Support runbook describing when to keep a case frontline versus when to escalate.",
                body=(
                    "Support Escalation Runbook\n"
                    "\n"
                    "Keep the case frontline when the user can complete recovery after one guided retry.\n"
                    "Escalate when identity ownership is uncertain, repeated reset attempts fail, or an active incident may be involved.\n"
                    "Every escalation packet should include customer impact, reproduction steps, known mitigations, and evidence references.\n"
                ),
            ),
        ),
        showcase_steps=(
            DemoShowcaseStep(
                title="Inspect the support knowledge base",
                description="Open the documents surface to see the KB article, incident note, and escalation runbook.",
                route_suffix="/documents",
                cta_label="Open documents",
            ),
            DemoShowcaseStep(
                title="Ask a support grounding question",
                description="Use chat to confirm which mitigation and escalation triggers appear in the seeded docs.",
                route_suffix="/chat",
                cta_label="Open chat",
                sample_prompt="Before escalating a password reset case, what should frontline support confirm and what mitigation can they offer immediately?",
            ),
            DemoShowcaseStep(
                title="Launch a support case workflow",
                description="Run a ticket summary or reply draft using the seeded support context, then inspect the resulting triage and escalation packet.",
                route_suffix="/tasks",
                cta_label="Open tasks",
                sample_task_type="ticket_summary",
                sample_task_input={
                    "customer_issue": "Customer says every password reset link is already expired, even after requesting a new email twice from mobile.",
                    "product_area": "Authentication",
                    "severity": "high",
                    "desired_outcome": "Restore access without forcing a full account recovery flow.",
                    "reproduction_steps": [
                        "Request a password reset email from the login page.",
                        "Open the email on a mobile device.",
                        "Tap the reset link and observe an expired-link message.",
                    ],
                },
            ),
        ),
    ),
    "job": DemoTemplate(
        template_id="job",
        module_type="job",
        title="Hiring Review Demo",
        summary="Seed a hiring packet, then use the Job Assistant to turn grounded materials into a structured candidate review.",
        workspace_name="Guided Demo - Hiring Review",
        workspace_description="Seeded hiring workspace for the public demo path.",
        seeded_documents=(
            DemoSeedDocument(
                title="backend-platform-role.txt",
                summary="Job description for a backend platform engineer focused on workflow systems and observability.",
                body=(
                    "Backend Platform Engineer Role\n"
                    "\n"
                    "Must-have skills: Python services, workflow orchestration, SQL, observability, and API design.\n"
                    "Preferred skills: retrieval systems, evaluation frameworks, and developer tooling.\n"
                    "The role owns internal workflow reliability and developer-facing platform primitives.\n"
                ),
            ),
            DemoSeedDocument(
                title="candidate-resume-lina.txt",
                summary="Condensed resume for a candidate with platform, workflow, and observability experience.",
                body=(
                    "Candidate Resume - Lina Chen\n"
                    "\n"
                    "Five years building Python backend services for internal developer platforms.\n"
                    "Led workflow reliability work across task orchestration, observability dashboards, and API integrations.\n"
                    "Less direct experience with evaluation systems, but strong grounding in platform operations and tooling.\n"
                ),
            ),
            DemoSeedDocument(
                title="hiring-rubric.txt",
                summary="Interview rubric focusing on system judgment, reliability ownership, and evidence-based tradeoffs.",
                body=(
                    "Hiring Rubric\n"
                    "\n"
                    "Strong candidates explain platform tradeoffs clearly, show ownership over reliability metrics, and can separate product asks from execution-layer design.\n"
                    "Interview focus areas: incident judgment, workflow state modeling, and collaboration with downstream product teams.\n"
                ),
            ),
        ),
        showcase_steps=(
            DemoShowcaseStep(
                title="Review the hiring packet",
                description="Open the documents surface and confirm the role brief, candidate resume, and rubric are already indexed.",
                route_suffix="/documents",
                cta_label="Open documents",
            ),
            DemoShowcaseStep(
                title="Ask a fit question",
                description="Use chat to quickly compare what the role requires with what the candidate has actually done.",
                route_suffix="/chat",
                cta_label="Open chat",
                sample_prompt="Which requirements in the backend platform role look strongest for Lina Chen, and where is the evidence thinner?",
            ),
            DemoShowcaseStep(
                title="Launch a candidate review",
                description="Run a resume match task to generate a structured fit assessment grounded in the seeded hiring materials.",
                route_suffix="/tasks",
                cta_label="Open tasks",
                sample_task_type="resume_match",
                sample_task_input={
                    "target_role": "Backend Platform Engineer",
                    "candidate_label": "Lina Chen",
                    "seniority": "mid-senior",
                    "must_have_skills": [
                        "Python backend services",
                        "workflow orchestration",
                        "SQL",
                        "observability",
                        "API design",
                    ],
                    "preferred_skills": [
                        "retrieval systems",
                        "evaluation frameworks",
                        "developer tooling",
                    ],
                    "hiring_context": "Hiring for a platform team that owns workflow reliability and developer-facing primitives.",
                },
            ),
        ),
    ),
}


def _serialize_template(template: DemoTemplate) -> PublicDemoTemplateResponse:
    return PublicDemoTemplateResponse(
        template_id=template.template_id,
        module_type=template.module_type,
        title=template.title,
        summary=template.summary,
        workspace_name=template.workspace_name,
        workspace_description=template.workspace_description,
        seeded_documents=[
            PublicDemoSeedDocumentResponse(title=document.title, summary=document.summary)
            for document in template.seeded_documents
        ],
        showcase_steps=[
            PublicDemoShowcaseStepResponse(
                title=step.title,
                description=step.description,
                route_suffix=step.route_suffix,
                cta_label=step.cta_label,
                sample_prompt=step.sample_prompt,
                sample_task_type=step.sample_task_type,
                sample_task_input=dict(step.sample_task_input),
            )
            for step in template.showcase_steps
        ],
    )


def list_public_demo_templates() -> list[PublicDemoTemplateResponse]:
    return [_serialize_template(template) for template in _DEMO_TEMPLATES.values()]


def get_public_demo_template(template_id: str) -> PublicDemoTemplateResponse:
    template = _DEMO_TEMPLATES.get(template_id)
    if template is None:
        raise ValueError("Public demo template not found")
    return _serialize_template(template)


def _require_demo_template(template_id: str) -> DemoTemplate:
    template = _DEMO_TEMPLATES.get(template_id)
    if template is None:
        raise ValueError("Public demo template not found")
    return template


def _ensure_template_fits_current_limits(template: DemoTemplate) -> None:
    settings = get_settings()
    if not settings.public_demo_mode:
        return

    if len(template.seeded_documents) > settings.public_demo_max_documents_per_workspace:
        raise PublicDemoLimitError(
            "Public demo limit reached: "
            f"the {template.title} template needs {len(template.seeded_documents)} seeded documents "
            f"but this environment allows only {settings.public_demo_max_documents_per_workspace}.",
        )


def create_public_demo_workspace(*, template_id: str, user_id: str) -> PublicDemoWorkspaceSeedResponse:
    template = _require_demo_template(template_id)
    _ensure_template_fits_current_limits(template)

    workspace = workspace_service.create_workspace(
        payload=WorkspaceCreate(
            name=template.workspace_name,
            module_type=template.module_type,
            description=template.workspace_description,
            module_config_json={
                "demo_template_id": template.template_id,
                "guided_demo": True,
            },
        ),
        owner_id=user_id,
    )

    documents = [
        document_service.create_text_document(
            workspace_id=workspace.id,
            user_id=user_id,
            title=document.title,
            text_content=document.body,
            source_type="demo_seed",
        )
        for document in template.seeded_documents
    ]

    return PublicDemoWorkspaceSeedResponse(
        workspace=workspace,
        documents=documents,
        template=_serialize_template(template),
    )
