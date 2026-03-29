import EvalManager from "../../../../components/evals/eval-manager";
import MetricsPanel from "../../../../components/workspace/metrics-panel";
import ObservabilityPanel from "../../../../components/workspace/observability-panel";
import WorkspacePageShell from "../../../../components/workspace/workspace-page-shell";

type WorkspacePageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceAnalyticsPage({ params }: WorkspacePageProps) {
  const { workspaceId } = params;

  return (
    <WorkspacePageShell
      description="这里保留评测、trace、readiness 和成本信息。它是复盘和验证入口，不是第一次进入工作区时的主路径。"
      page="analytics"
      title="分析"
      workspaceId={workspaceId}
    >
      <MetricsPanel workspaceId={workspaceId} />
      <EvalManager workspaceId={workspaceId} />
      <ObservabilityPanel workspaceId={workspaceId} />
    </WorkspacePageShell>
  );
}
