import Link from "next/link";

import PublicDemoNotice from "../components/public-demo/public-demo-notice";
import SectionCard from "../components/ui/section-card";
import { getHealth, getPublicDemoSettings, getPublicDemoTemplates, getScenarioModules } from "../lib/api";
import { platformCoreModule } from "../lib/navigation";

const MODULE_PRODUCT_NAMES: Record<string, string> = {
  research: "Research Assistant",
  support: "Support Copilot",
  job: "Job Assistant",
};

function getModuleDisplayName(moduleType: string): string {
  return MODULE_PRODUCT_NAMES[moduleType] ?? moduleType;
}

export default async function Home() {
  const [health, publicDemoResponse, demoTemplatesResponse, scenarioModulesResponse] = await Promise.all([
    getHealth(),
    getPublicDemoSettings(),
    getPublicDemoTemplates(),
    getScenarioModules(),
  ]);
  const scenarioModules = Array.isArray(scenarioModulesResponse) ? scenarioModulesResponse : [];
  const publicDemoSettings =
    publicDemoResponse && "public_demo_mode" in publicDemoResponse ? publicDemoResponse : null;
  const demoTemplates = Array.isArray(demoTemplatesResponse) ? demoTemplatesResponse : [];
  const platformModules = [
    platformCoreModule,
    ...scenarioModules.map((module) => ({
      title: module.title,
      description: module.description,
    })),
  ];

  return (
    <main>
      <h1>AI 工作流工作台</h1>
      <p>一个基于共享运行时的 AI 工作流平台，提供文档 grounding、场景工作流、任务、评测与可观测能力。</p>
      <p>
        API 健康状态：<strong>{health.status}</strong>
      </p>

      {publicDemoSettings ? <PublicDemoNotice settings={publicDemoSettings} /> : null}

      <SectionCard
        title="30 秒读懂"
        description="这个仓库已经不只是本地实验环境。Stage D 已把它推进成一个共享运行时之上的公网 demo，并承载三个模块工作流。"
      >
        <ul>
          <li>Research Assistant 会把预置资料库转成有依据的综合分析与报告。</li>
          <li>Support Copilot 会把知识库上下文转成案例分诊、回复草稿和升级交接包。</li>
          <li>Job Assistant 会把招聘材料转成有依据的匹配评估和候选人 shortlist 工作流。</li>
        </ul>
      </SectionCard>

      <SectionCard
        title="引导演示路径"
        description="如果你想快速理解系统，而不是从空白工作区开始，可以直接选择下面这些带预置内容的模块路径。"
      >
        {demoTemplates.length === 0 ? <p>当前暂时没有可用的引导演示模板。</p> : null}
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          }}
        >
          {demoTemplates.map((template) => (
            <div
              key={template.template_id}
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 12,
                padding: 16,
              }}
            >
              <div style={{ alignItems: "center", display: "flex", gap: 8, marginBottom: 8 }}>
                <strong>{template.title}</strong>
                <span
                  style={{
                    backgroundColor: "#0f172a12",
                    borderRadius: 999,
                    color: "#0f172a",
                    fontSize: 12,
                    fontWeight: 600,
                    padding: "2px 10px",
                    textTransform: "uppercase",
                  }}
                >
                  {getModuleDisplayName(template.module_type)}
                </span>
              </div>
              <p style={{ marginTop: 0 }}>{template.summary}</p>
              <p style={{ marginBottom: 8, marginTop: 0 }}>
                <strong>预置文档：</strong> {template.seeded_documents.map((document) => document.title).join("，")}
              </p>
              <p style={{ marginBottom: 12, marginTop: 0 }}>
                <strong>演示步骤：</strong> {template.showcase_steps.length}
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
                <Link href="/register">注册</Link>
                <Link href="/login">登录</Link>
                <Link href="/workspaces">工作区中心</Link>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="你可以体验什么"
        description="Stage D 的重点是把公网 demo 路径做清楚，而不是默认依赖本地运维者的隐式准备。"
      >
        <ul>
          <li>当公网自助注册开放时，可以直接注册或登录。</li>
          <li>可以创建引导演示工作区，也可以手动创建 Research、Support、Job 三类 workflow 的工作区。</li>
          <li>查看预置文档、提出 grounded 问题，并启动模块任务。</li>
          <li>直接查看评测、任务和模块页面，不依赖隐藏的运维专用步骤。</li>
        </ul>
      </SectionCard>

      <SectionCard title="平台模块" description="这些模块共享同一套工作区、运行时和 API 核心。">
        <ul>
          {platformModules.map((module) => (
            <li key={module.title}>
              <strong>{module.title}</strong>：{module.description}
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard title="继续探索">
        <ul>
          <li>
            <Link href="/dashboard">仪表盘</Link>
          </li>
          <li>
            <Link href="/workspaces">工作区中心</Link>
          </li>
          <li>
            <Link href="/register">注册</Link>
          </li>
          <li>
            <Link href="/login">登录</Link>
          </li>
        </ul>
      </SectionCard>
    </main>
  );
}
