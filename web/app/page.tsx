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
        title="Current Phase: Phase 0"
        description="The repository is in Scaffold & Alignment: docs, Docker, CI, and route/page scaffolds are aligned with the platform roadmap."
      >
        <ul>
          <li>Phase 0 demo APIs: health, workspaces, chat, metrics</li>
          <li>Scaffolded APIs reserved for later phases: auth, documents, tasks, agents, evals</li>
          <li>Phase 1 target: auth boundary, workspace persistence, document API surface, trace and metrics loop</li>
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
            <Link href="/workspaces/demo/chat">Demo Chat View</Link>
          </li>
          <li>
            <Link href="/workspaces/demo/documents">Demo Documents View</Link>
          </li>
          <li>
            <Link href="/login">Auth Entry</Link>
          </li>
        </ul>
      </SectionCard>
    </main>
  );
}
