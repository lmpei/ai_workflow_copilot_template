import Link from "next/link";

import PublicDemoNotice from "../components/public-demo/public-demo-notice";
import SectionCard from "../components/ui/section-card";
import { getHealth, getPublicDemoSettings, getPublicDemoTemplates, getScenarioModules } from "../lib/api";
import { platformCoreModule } from "../lib/navigation";

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
      <h1>AI Workflow Workbench</h1>
      <p>
        Public-demo baseline for a shared AI workflow platform with document grounding, scenario workflows,
        tasks, evals, and observability.
      </p>
      <p>
        API health: <strong>{health.status}</strong>
      </p>

      {publicDemoSettings ? <PublicDemoNotice settings={publicDemoSettings} /> : null}

      <SectionCard
        title="30-Second Read"
        description="This repo is no longer just a local sandbox. Stage D turns it into a public-facing demo with one shared runtime and three module workflows."
      >
        <ul>
          <li>Research Assistant turns a seeded corpus into grounded synthesis and reports.</li>
          <li>Support Copilot turns knowledge-base context into case triage, reply drafts, and escalation packets.</li>
          <li>Job Assistant turns hiring materials into grounded fit reviews and shortlist-oriented workflow steps.</li>
        </ul>
      </SectionCard>

      <SectionCard
        title="Guided Demo Paths"
        description="Use one of these seeded module paths when you want to understand the system quickly instead of starting from an empty workspace."
      >
        {demoTemplates.length === 0 ? <p>Guided demo templates are not available right now.</p> : null}
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
                  {template.module_type}
                </span>
              </div>
              <p style={{ marginTop: 0 }}>{template.summary}</p>
              <p style={{ marginBottom: 8, marginTop: 0 }}>
                <strong>Seeded documents:</strong> {template.seeded_documents.map((document) => document.title).join(", ")}
              </p>
              <p style={{ marginBottom: 12, marginTop: 0 }}>
                <strong>Showcase steps:</strong> {template.showcase_steps.length}
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
                <Link href="/register">Register</Link>
                <Link href="/login">Login</Link>
                <Link href="/workspaces">Workspace Hub</Link>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="What You Can Try"
        description="Stage D is focused on making the public demo path explicit instead of assuming local operator setup."
      >
        <ul>
          <li>Create an account or sign in when public self-serve registration is available.</li>
          <li>Create a guided demo workspace or a manual workspace for Research, Support, or Job workflows.</li>
          <li>Inspect seeded documents, ask grounded chat questions, and launch module-specific tasks.</li>
          <li>Inspect eval, task, and module surfaces without relying on hidden operator-only steps.</li>
        </ul>
      </SectionCard>

      <SectionCard title="Platform Modules" description="These modules share one common workspace, runtime, and API core.">
        <ul>
          {platformModules.map((module) => (
            <li key={module.title}>
              <strong>{module.title}</strong>: {module.description}
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard title="Explore the Demo">
        <ul>
          <li>
            <Link href="/dashboard">Dashboard</Link>
          </li>
          <li>
            <Link href="/workspaces">Workspace Hub</Link>
          </li>
          <li>
            <Link href="/register">Register</Link>
          </li>
          <li>
            <Link href="/login">Login</Link>
          </li>
        </ul>
      </SectionCard>
    </main>
  );
}