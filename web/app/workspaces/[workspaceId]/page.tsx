import GuidedWorkspaceShowcase from "../../../components/public-demo/guided-workspace-showcase";
import ModuleHubPanel from "../../../components/workspace/module-hub-panel";
import SectionCard from "../../../components/ui/section-card";
import WorkspaceNav from "../../../components/workspace/workspace-nav";

type WorkspacePageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceOverviewPage({ params }: WorkspacePageProps) {
  const { workspaceId } = params;

  return (
    <main>
      <h1>工作区概览</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <GuidedWorkspaceShowcase workspaceId={workspaceId} />
      <SectionCard
        title="共享工作区面板"
        description="每个模块都会把文档、对话痕迹、任务和分析统一收在同一个工作区范围内。"
      >
        <ul>
          <li>文档与检索状态</li>
          <li>对话与引用来源</li>
          <li>任务、agent 执行与工具痕迹</li>
          <li>质量指标与成本跟踪</li>
        </ul>
      </SectionCard>
      <ModuleHubPanel workspaceId={workspaceId} />
    </main>
  );
}
