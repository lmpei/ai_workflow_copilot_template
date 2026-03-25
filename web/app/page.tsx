import Link from "next/link";

import PublicDemoNotice from "../components/public-demo/public-demo-notice";
import SectionCard from "../components/ui/section-card";
import { getHealth, getPublicDemoSettings, getScenarioModules } from "../lib/api";
import { platformCoreModule } from "../lib/navigation";

export default async function Home() {
  const [health, publicDemoResponse, scenarioModulesResponse] = await Promise.all([
    getHealth(),
    getPublicDemoSettings(),
    getScenarioModules(),
  ]);
  const scenarioModules = Array.isArray(scenarioModulesResponse) ? scenarioModulesResponse : [];
  const publicDemoSettings =
    publicDemoResponse && "public_demo_mode" in publicDemoResponse ? publicDemoResponse : null;
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
        title="What You Can Try"
        description="Stage D is focused on making the public demo path explicit instead of assuming local setup."
      >
        <ul>
          <li>Create an account or sign in when public self-serve registration is available</li>
          <li>Create authenticated workspaces for Research, Support, or Job workflows</li>
          <li>Upload documents, run grounded chat, and launch scenario tasks inside each workspace</li>
          <li>Inspect eval, task, and module surfaces without relying on hidden operator-only steps</li>
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
