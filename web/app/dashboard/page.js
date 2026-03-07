import SectionCard from "../../components/ui/section-card";
import { platformModules } from "../../lib/navigation";

export default function DashboardPage() {
  return (
    <main>
      <h1>Platform Dashboard</h1>
      <p>This area will evolve into the control plane for workspaces, tasks, and metrics.</p>
      {platformModules.map((module) => (
        <SectionCard
          key={module.title}
          title={module.title}
          description={module.description}
        />
      ))}
    </main>
  );
}
