import SectionCard from "../../components/ui/section-card";
import { getScenarioModules } from "../../lib/api";
import { platformCoreModule } from "../../lib/navigation";

export default async function DashboardPage() {
  const scenarioModulesResponse = await getScenarioModules();
  const scenarioModules = Array.isArray(scenarioModulesResponse) ? scenarioModulesResponse : [];
  const platformModules = [
    platformCoreModule,
    ...scenarioModules.map((module) => ({
      title: module.title,
      description: module.description,
    })),
  ];

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