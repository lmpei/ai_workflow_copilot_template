import EvalManager from "../../../../components/evals/eval-manager";
import MetricsPanel from "../../../../components/workspace/metrics-panel";
import ObservabilityPanel from "../../../../components/workspace/observability-panel";
import WorkspaceNav from "../../../../components/workspace/workspace-nav";

type WorkspacePageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceAnalyticsPage({ params }: WorkspacePageProps) {
  const { workspaceId } = params;

  return (
    <main>
      <h1>分析</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <p>这里汇总工作区级的评测数据、近期 traces、基础指标与 readiness 视图。</p>
      <MetricsPanel workspaceId={workspaceId} />
      <EvalManager workspaceId={workspaceId} />
      <ObservabilityPanel workspaceId={workspaceId} />
    </main>
  );
}
