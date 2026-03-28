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
        title="Research 简报演示",
        summary="创建一个带有预置启动材料的 grounded 研究工作区，再把整套语料转成简洁简报。",
        workspace_name="引导演示 - Research 简报",
        workspace_description="用于公开演示路径的预置 Research 工作区。",
        seeded_documents=(
            DemoSeedDocument(
                title="产品启动备忘录.txt",
                summary="描述试点目标、范围和上线风险的内部产品备忘录。",
                body=(
                    "Acme 团队收件箱试点启动备忘录\n"
                    "\n"
                    "目标：在第三季度为小型支持团队上线共享团队收件箱试点。\n"
                    "核心价值：缩短高容量支持队列的响应时间。\n"
                    "已知风险：上手复杂、路由归属不清，以及分析覆盖有限。\n"
                    "成功指标：首次响应时间低于 20 分钟，积压量下降 25%。\n"
                    "待解决担忧：当前路由逻辑无法解释工单为什么会在队友之间流转。\n"
                ),
            ),
            DemoSeedDocument(
                title="客户访谈纪要.txt",
                summary="来自试点客户的精简访谈纪要，描述摩擦点和期望结果。",
                body=(
                    "试点客户访谈纪要\n"
                    "\n"
                    "客户 A 希望看到路由解释，因为管理者需要审计工单交接。\n"
                    "客户 B 表示，当同一个案例同时命中多条收件箱规则时，配置过程会变得混乱。\n"
                    "客户 C 很看重 SLA 可见性，希望更清楚地看到超时会话报告。\n"
                    "三位客户都提到，如果管理员不能快速解释归属变化，推广就会停滞。\n"
                ),
            ),
            DemoSeedDocument(
                title="竞品观察.txt",
                summary="简要市场扫描，覆盖竞品在共享收件箱工具上的优势与缺口。",
                body=(
                    "竞品观察\n"
                    "\n"
                    "Northstar 强调审计日志和适合审批流程的路由变更。\n"
                    "Relay 的差异化在于面向积压、SLA 违约和交接原因的分析面板。\n"
                    "两家竞品在配置简洁性上都不算突出，但都把路由可见性讲得很清楚。\n"
                ),
            ),
        ),
        showcase_steps=(
            DemoShowcaseStep(
                title="查看预置语料",
                description="打开文档页面，确认演示工作区已经带有已索引的源材料。",
                route_suffix="/documents",
                cta_label="打开文档",
            ),
            DemoShowcaseStep(
                title="提出 grounded 问题",
                description="使用 chat 验证回答是否引用了预置启动材料，而不是脱离材料自由发挥。",
                route_suffix="/chat",
                cta_label="打开对话",
                sample_prompt="这个团队收件箱试点最突出的上线风险是什么？分别有哪些文档能支撑这些判断？",
            ),
            DemoShowcaseStep(
                title="运行研究任务",
                description="启动一个结构化研究摘要，把同一套语料转成有证据支撑的简报。",
                route_suffix="/tasks",
                cta_label="打开任务",
                sample_task_type="research_summary",
                sample_task_input={
                    "goal": "总结关于试点上线风险的关键证据，并为上线评审给出下一步建议。",
                    "focus_areas": ["上线风险", "路由可见性", "分析就绪度"],
                    "key_questions": [
                        "什么因素会阻碍推广信心？",
                        "哪些证据指向最大的运营缺口？",
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
        title="Support 升级演示",
        summary="预置一个支持知识库，然后从一线分诊一路走到 grounded 升级交接包。",
        workspace_name="引导演示 - Support 升级",
        workspace_description="用于公开演示路径的预置 Support 工作区。",
        seeded_documents=(
            DemoSeedDocument(
                title="密码重置知识库.txt",
                summary="关于重置链接、账号归属校验和安全重发规则的知识库说明。",
                body=(
                    "密码重置知识库\n"
                    "\n"
                    "重置链接会在 30 分钟后失效。\n"
                    "一线支持在通过最近一次成功登录时间或账单邮编确认账号归属后，可以重发重置链接。\n"
                    "如果同一用户在一小时内多次反馈链接过期，应升级给身份工程团队，因为可能涉及邮件跳转不匹配。\n"
                ),
            ),
            DemoSeedDocument(
                title="事故更新.txt",
                summary="描述一次 token 校验发布后出现间歇性过期行为的事故更新。",
                body=(
                    "事故更新 - 身份 Token 校验\n"
                    "\n"
                    "周二的一次发布导致在移动邮件客户端中打开重置链接时，间歇性出现误报过期。\n"
                    "影响范围有限，但问题尚未解决。\n"
                    "临时缓解措施：建议用户重新申请链接，并在系统浏览器中打开。\n"
                ),
            ),
            DemoSeedDocument(
                title="升级处理手册.txt",
                summary="描述何时由一线继续处理、何时应升级的支持手册。",
                body=(
                    "Support 升级处理手册\n"
                    "\n"
                    "如果用户在一次引导重试后就能恢复访问，应继续由一线处理。\n"
                    "当身份归属不确定、多次重置失败，或可能涉及活动事故时，应升级处理。\n"
                    "每份升级交接包都应包含客户影响、复现步骤、已知缓解措施和证据引用。\n"
                ),
            ),
        ),
        showcase_steps=(
            DemoShowcaseStep(
                title="查看支持知识库",
                description="打开文档页面，查看知识库文章、事故说明和升级手册。",
                route_suffix="/documents",
                cta_label="打开文档",
            ),
            DemoShowcaseStep(
                title="提出支持 grounding 问题",
                description="使用 chat 确认预置文档里提到了哪些缓解措施和升级触发条件。",
                route_suffix="/chat",
                cta_label="打开对话",
                sample_prompt="在升级一个密码重置案例之前，一线支持需要先确认什么？又可以立刻提供什么缓解方案？",
            ),
            DemoShowcaseStep(
                title="启动支持案例流程",
                description="基于预置的支持上下文运行工单摘要或回复草稿，再查看生成的分诊结果和升级交接包。",
                route_suffix="/tasks",
                cta_label="打开任务",
                sample_task_type="ticket_summary",
                sample_task_input={
                    "customer_issue": "客户反馈每一封密码重置邮件里的链接都已经过期，即使他在手机上连续重新申请了两次。",
                    "product_area": "身份认证",
                    "severity": "high",
                    "desired_outcome": "恢复访问能力，但不要强迫客户走完整账号找回流程。",
                    "reproduction_steps": [
                        "在登录页请求密码重置邮件。",
                        "在移动设备上打开邮件。",
                        "点击重置链接，并看到链接已过期的提示。",
                    ],
                },
            ),
        ),
    ),
    "job": DemoTemplate(
        template_id="job",
        module_type="job",
        title="招聘评审演示",
        summary="预置一份招聘材料包，再用 Job Assistant 把 grounded 材料转成结构化候选人评审。",
        workspace_name="引导演示 - 招聘评审",
        workspace_description="用于公开演示路径的预置 Job 工作区。",
        seeded_documents=(
            DemoSeedDocument(
                title="后端平台岗位说明.txt",
                summary="聚焦工作流系统与可观测性的后端平台工程师岗位说明。",
                body=(
                    "后端平台工程师岗位说明\n"
                    "\n"
                    "必备技能：Python 服务、工作流编排、SQL、可观测性和 API 设计。\n"
                    "加分技能：检索系统、评测框架和开发者工具。\n"
                    "这个岗位负责内部工作流稳定性，以及面向开发者的平台基础能力。\n"
                ),
            ),
            DemoSeedDocument(
                title="候选人简历-李娜.txt",
                summary="一位具备平台、工作流和可观测性经验候选人的精简简历。",
                body=(
                    "候选人简历 - Lina Chen\n"
                    "\n"
                    "有五年为内部开发者平台构建 Python 后端服务的经验。\n"
                    "曾负责工作流稳定性相关工作，覆盖任务编排、可观测面板和 API 集成。\n"
                    "对评测系统的直接经验较少，但在平台运维和工具建设方面基础扎实。\n"
                ),
            ),
            DemoSeedDocument(
                title="招聘评审标准.txt",
                summary="聚焦系统判断、稳定性 owner 能力和基于证据取舍的面试标准。",
                body=(
                    "招聘评审标准\n"
                    "\n"
                    "优秀候选人应能清楚解释平台取舍，对稳定性指标有 owner 意识，并能区分产品诉求与执行层设计。\n"
                    "面试重点：事故判断、工作流状态建模，以及与下游产品团队协作。\n"
                ),
            ),
        ),
        showcase_steps=(
            DemoShowcaseStep(
                title="查看招聘材料包",
                description="打开文档页面，确认岗位说明、候选人简历和评审标准都已经完成索引。",
                route_suffix="/documents",
                cta_label="打开文档",
            ),
            DemoShowcaseStep(
                title="提出匹配问题",
                description="使用 chat 快速比较岗位要求和候选人的真实经历。",
                route_suffix="/chat",
                cta_label="打开对话",
                sample_prompt="在后端平台岗位的要求里，Lina Chen 最强的匹配点是什么？哪些地方的证据还偏弱？",
            ),
            DemoShowcaseStep(
                title="启动候选人评审",
                description="运行一个简历匹配任务，基于预置招聘材料生成结构化匹配评估。",
                route_suffix="/tasks",
                cta_label="打开任务",
                sample_task_type="resume_match",
                sample_task_input={
                    "target_role": "后端平台工程师",
                    "candidate_label": "Lina Chen",
                    "seniority": "mid-senior",
                    "must_have_skills": [
                        "Python 后端服务",
                        "工作流编排",
                        "SQL",
                        "可观测性",
                        "API 设计",
                    ],
                    "preferred_skills": [
                        "检索系统",
                        "评测框架",
                        "开发者工具",
                    ],
                    "hiring_context": "为负责工作流稳定性和开发者基础能力的平台团队招聘。",
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
        raise ValueError("未找到 public demo 模板")
    return _serialize_template(template)


def _require_demo_template(template_id: str) -> DemoTemplate:
    template = _DEMO_TEMPLATES.get(template_id)
    if template is None:
        raise ValueError("未找到 public demo 模板")
    return template


def _ensure_template_fits_current_limits(template: DemoTemplate) -> None:
    settings = get_settings()
    if not settings.public_demo_mode:
        return

    if len(template.seeded_documents) > settings.public_demo_max_documents_per_workspace:
        raise PublicDemoLimitError(
            "已达到 public demo 限额："
            f"模板 {template.title} 需要 {len(template.seeded_documents)} 份预置文档，"
            f"但当前环境只允许 {settings.public_demo_max_documents_per_workspace} 份。",
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
