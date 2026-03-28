import type { CSSProperties } from "react";
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

const MODULE_ENTRY_GUIDES: Record<string, { fit: string; output: string }> = {
  research: {
    fit: "适合把多份资料整理成一份有依据的综合分析。",
    output: "常见结果：综合分析、观点对比、workspace 报告。",
  },
  support: {
    fit: "适合处理客户问题、知识库问答、回复草稿和升级判断。",
    output: "常见结果：case 摘要、回复草稿、升级交接信息。",
  },
  job: {
    fit: "适合处理岗位要求、候选人材料、比较和短名单更新。",
    output: "常见结果：匹配评估、候选人比较、shortlist 建议。",
  },
};

const HERO_PANEL_STYLE: CSSProperties = {
  border: "1px solid #cbd5e1",
  borderRadius: 16,
  display: "grid",
  gap: 12,
  padding: 20,
};

const CTA_LINK_STYLE: CSSProperties = {
  backgroundColor: "#0f172a",
  borderRadius: 999,
  color: "#ffffff",
  display: "inline-flex",
  fontWeight: 600,
  padding: "10px 16px",
  textDecoration: "none",
};

const SECONDARY_LINK_STYLE: CSSProperties = {
  color: "#0f172a",
  display: "inline-flex",
  fontWeight: 600,
  textDecoration: "underline",
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
  const primaryStartHref = publicDemoSettings?.registration_enabled === true ? "/register" : "/login";
  const primaryStartLabel = publicDemoSettings?.registration_enabled === true ? "注册后开始体验" : "登录后开始体验";

  return (
    <main style={{ display: "grid", gap: 16 }}>
      <h1>AI 工作流工作台</h1>
      <p>先从一条清晰的演示路径开始，再逐步进入文档、对话、任务和 workbench，而不是一次理解全部平台结构。</p>

      <section
        style={{
          background: "linear-gradient(135deg, rgba(15,23,42,0.04), rgba(14,116,144,0.08))",
          border: "1px solid #cbd5e1",
          borderRadius: 20,
          display: "grid",
          gap: 16,
          padding: 24,
        }}
      >
        <div style={{ display: "grid", gap: 8 }}>
          <strong style={{ color: "#0f172a" }}>建议你先这样开始</strong>
          <div>第一次体验时，不需要先理解所有页面。先注册或登录，然后到工作区中心创建一条引导演示路径。</div>
        </div>
        <div
          style={{
            display: "grid",
            gap: 16,
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          }}
        >
          <div style={HERO_PANEL_STYLE}>
            <strong>第一次体验</strong>
            <div>先获得账号，再进入工作区中心创建引导演示工作区。这样你会直接看到预置文档、示例提问和建议任务输入。</div>
            <ol style={{ margin: 0, paddingLeft: 20 }}>
              <li>注册或登录</li>
              <li>进入工作区中心</li>
              <li>选择一条引导演示路径</li>
            </ol>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
              <Link href={primaryStartHref} style={CTA_LINK_STYLE}>
                {primaryStartLabel}
              </Link>
              <Link href="/workspaces" style={SECONDARY_LINK_STYLE}>
                先看工作区中心
              </Link>
            </div>
          </div>
          <div style={HERO_PANEL_STYLE}>
            <strong>继续已有工作</strong>
            <div>如果你已经有账号或已有工作区，直接回到工作区中心。Support 和 Job 的已有工作会从已有 case 或 hiring packet 继续。</div>
            <div style={{ color: "#475569" }}>不需要重新创建空白工作区，也不需要从首页自己拼路径。</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
              <Link href="/workspaces" style={CTA_LINK_STYLE}>
                进入工作区中心
              </Link>
              <Link href="/login" style={SECONDARY_LINK_STYLE}>
                先登录
              </Link>
            </div>
          </div>
        </div>
      </section>

      <SectionCard
        title="三个模块分别适合什么"
        description="先按你要解决的问题选模块，不需要先理解整个共享平台。"
      >
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          }}
        >
          {Object.entries(MODULE_PRODUCT_NAMES).map(([moduleType, moduleName]) => (
            <div
              key={moduleType}
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 14,
                display: "grid",
                gap: 8,
                padding: 16,
              }}
            >
              <strong>{moduleName}</strong>
              <div>{MODULE_ENTRY_GUIDES[moduleType]?.fit}</div>
              <div style={{ color: "#475569" }}>{MODULE_ENTRY_GUIDES[moduleType]?.output}</div>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="推荐的三条演示路径"
        description="这三条路径都从工作区中心创建。现在只需要知道你想看哪一类问题，不需要先记住所有细节。"
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
                borderRadius: 14,
                display: "grid",
                gap: 10,
                padding: 16,
              }}
            >
              <div style={{ alignItems: "center", display: "flex", gap: 8, marginBottom: 4 }}>
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
              <div>{template.summary}</div>
              <div style={{ color: "#475569" }}>创建后按“文档 - 对话 - 任务”的顺序走，就能看懂这条路径。</div>
              <Link href="/workspaces" style={SECONDARY_LINK_STYLE}>
                去工作区中心创建这条路径
              </Link>
              <details>
                <summary>查看预置文档和步骤</summary>
                <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
                  <div>
                    <strong>预置文档：</strong> {template.seeded_documents.map((document) => document.title).join("，")}
                  </div>
                  <div>
                    <strong>演示步骤：</strong> {template.showcase_steps.map((step) => step.title).join(" -> ")}
                  </div>
                </div>
              </details>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="更多平台信息" description="下面这些信息保留给需要进一步确认的人，不再放在首屏主路径里。">
        <div style={{ display: "grid", gap: 12 }}>
          {publicDemoSettings ? (
            <details>
              <summary>查看当前 demo 限制</summary>
              <div style={{ marginTop: 12 }}>
                <PublicDemoNotice
                  description="这些限制是为了让公网演示保持可控，并不影响你先按推荐路径体验系统。"
                  settings={publicDemoSettings}
                  title=""
                  variant="compact"
                />
              </div>
            </details>
          ) : null}
          <details>
            <summary>查看系统状态和平台背景</summary>
            <div style={{ display: "grid", gap: 12, marginTop: 12 }}>
              <div>
                API 健康状态：<strong>{health.status}</strong>
              </div>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {platformModules.map((module) => (
                  <li key={module.title}>
                    <strong>{module.title}</strong>：{module.description}
                  </li>
                ))}
              </ul>
            </div>
          </details>
        </div>
      </SectionCard>
    </main>
  );
}
