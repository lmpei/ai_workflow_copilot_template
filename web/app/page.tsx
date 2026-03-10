import Link from "next/link";

import SectionCard from "../components/ui/section-card";
import { getHealth } from "../lib/api";
import { platformModules } from "../lib/navigation";

export default async function Home() {
  const health = await getHealth();
  return (
    <main>
      <h1>AI Workflow Copilot</h1>
      <p>AI workflow platform scaffold for document ingest, retrieval, agents, tasks, and observability.</p>
      <p>
        API health: <strong>{health.status}</strong>
      </p>

      <SectionCard
        title="Platform MVP Surfaces"
        description="The frontend now connects to the Phase 1 auth, workspace, document, chat, and metrics APIs."
      >
        <ul>
          <li>Register and sign in from the frontend</li>
          <li>Create and open authenticated workspaces</li>
          <li>Upload documents, submit chat prompts, and inspect workspace metrics</li>
          <li>Tasks, agents, and eval dashboards remain reserved for later phases</li>
        </ul>
      </SectionCard>

      <SectionCard title="Platform Modules" description="These modules share one common workspace and API core.">
        <ul>
          {platformModules.map((module) => (
            <li key={module.title}>
              <strong>{module.title}</strong>: {module.description}
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard title="Explore the Scaffold">
        <ul>
          <li>
            <Link href="/dashboard">Dashboard</Link>
          </li>
          <li>
            <Link href="/workspaces">Workspaces</Link>
          </li>
          <li>
            <Link href="/register">Register</Link>
          </li>
          <li>
            <Link href="/login">Login</Link>
          </li>
          <li>
            <Link href="/workspaces">Workspace Hub</Link>
          </li>
        </ul>
      </SectionCard>
    </main>
  );
}
