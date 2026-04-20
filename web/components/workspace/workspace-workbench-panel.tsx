"use client";

import { useCallback, useEffect, useState } from "react";

import { getWorkspace, isApiClientError } from "../../lib/api";
import type { JobHiringPacketContinuationDraft, ModuleType, Workspace } from "../../lib/types";
import type { SupportCaseContinuationDraft } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import ChatPanel from "../chat/chat-panel";
import DocumentManager from "../documents/document-manager";
import JobAssistantActionPanel from "../job/job-assistant-action-panel";
import JobHiringWorkbenchSection from "../job/job-hiring-workbench-section";
import AiFrontierRecordsPanel from "../research/ai-frontier-records-panel";
import SupportCaseWorkbenchSection from "../support/support-case-workbench-section";
import SupportCopilotPanel from "../support/support-copilot-panel";
import SectionCard from "../ui/section-card";

type WorkspaceWorkbenchPanelProps = {
  workspaceId: string;
  initialPanel?: string;
  workspaceOverride?: Workspace | null;
};

const MODULE_PRODUCT_NAMES: Record<ModuleType, string> = {
  research: "AI 热点追踪",
  support: "Support Copilot",
  job: "Job Assistant",
};

function getModuleDisplayName(moduleType?: string | null): string {
  if (!moduleType) {
    return "未配置模块";
  }

  return MODULE_PRODUCT_NAMES[moduleType as ModuleType] ?? moduleType;
}

function ResearchWorkbench({ workspace, workspaceId }: { workspace: Workspace; workspaceId: string }) {
  return (
    <div style={{ display: "grid", gap: 22 }}>
      <section
        style={{
          background:
            "radial-gradient(circle at top right, rgba(8,145,178,0.18), transparent 26%), linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)",
          border: "1px solid #dbe4f0",
          borderRadius: 28,
          display: "grid",
          gap: 14,
          overflow: "hidden",
          padding: 24,
          position: "relative",
        }}
      >
        <div
          style={{
            background:
              "linear-gradient(135deg, rgba(15,23,42,0.96) 0%, rgba(8,47,73,0.96) 100%)",
            borderRadius: 18,
            color: "#f8fafc",
            display: "grid",
            gap: 10,
            maxWidth: 760,
            padding: 20,
          }}
        >
          <span
            style={{
              color: "#bae6fd",
              fontSize: 12,
              fontWeight: 800,
              letterSpacing: "0.16em",
              textTransform: "uppercase",
            }}
          >
            AI Signal Tracker
          </span>
          <h1 style={{ fontSize: "clamp(2.2rem, 4vw, 3.5rem)", lineHeight: 1, margin: 0 }}>AI 热点追踪</h1>
          <p style={{ color: "rgba(248,250,252,0.86)", lineHeight: 1.8, margin: 0 }}>
            围绕最新高可信来源跟踪 AI 行业、产品、模型与开源生态的变化，把动态沉淀成可回看的判断。
          </p>
        </div>

        <div
          style={{
            color: "#475569",
            display: "grid",
            gap: 8,
            maxWidth: 760,
          }}
        >
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            <span
              style={{
                backgroundColor: "#ecfeff",
                borderRadius: 999,
                color: "#0f172a",
                fontSize: 12,
                fontWeight: 700,
                padding: "6px 10px",
              }}
            >
              工作区：{workspace.name}
            </span>
            {workspace.module_config_json.guided_demo === true ? (
              <span
                style={{
                  backgroundColor: "#f8fafc",
                  borderRadius: 999,
                  color: "#475569",
                  fontSize: 12,
                  fontWeight: 700,
                  padding: "6px 10px",
                }}
              >
                引导演示工作区
              </span>
            ) : null}
          </div>
          <p style={{ lineHeight: 1.8, margin: 0 }}>
            默认路径只保留来源、当前结果和历史记录。追踪、评估和底层协议状态不再占据主工作台。
          </p>
        </div>
      </section>

      <section
        style={{
          alignItems: "start",
          display: "grid",
          gap: 20,
          gridTemplateColumns: "minmax(0, 1.25fr) minmax(320px, 0.75fr)",
        }}
      >
        <ChatPanel
          assistantLabel="AI 热点追踪"
          defaultMode="research_external_context"
          introBody="从一个当前值得关注的问题开始。系统会围绕可用来源组织摘要、判断和项目观察，而不是把内部分析过程直接摊给你。"
          introTitle="开始一次追踪"
          outputTitle="本次追踪"
          placeholder="例如：总结最近 Agent、MCP 和开源框架的变化，并指出哪些项目值得继续跟进。"
          primaryActionLabel="开始追踪"
          showConnectorControls={false}
          showModePicker={false}
          showRecentRecords={false}
          showSnapshotPicker={false}
          showToolSteps={false}
          suggestedPrompts={[
            "总结最近最值得关注的 AI 热点变化。",
            "指出当前最值得持续跟进的主题、事件和项目。",
            "告诉我哪些判断还需要更多原始来源来验证。",
          ]}
          supportsBackgroundRuns={false}
          workflowLabel="AI Signal Tracker"
          workspaceId={workspaceId}
        />

        <section
          style={{
            backgroundColor: "#ffffff",
            border: "1px solid #dbe4f0",
            borderRadius: 24,
            display: "grid",
            gap: 14,
            padding: 18,
          }}
        >
          <div style={{ display: "grid", gap: 6 }}>
            <span
              style={{
                color: "#64748b",
                fontSize: 12,
                fontWeight: 800,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
              }}
            >
              Source Intake
            </span>
            <strong style={{ color: "#0f172a", fontSize: 18 }}>来源与资料</strong>
            <p style={{ color: "#475569", lineHeight: 1.8, margin: 0 }}>
              放入工作区资料或补充材料。系统会在可用时自动结合外部最新来源，但不会把技术开关暴露给主路径。
            </p>
          </div>
          <DocumentManager variant="dock" workspaceId={workspaceId} />
        </section>
      </section>

      <AiFrontierRecordsPanel workspaceId={workspaceId} />
    </div>
  );
}

function SupportWorkbench({ workspaceId }: { workspaceId: string }) {
  const { session } = useAuthSession();
  const [continuationDraft, setContinuationDraft] = useState<SupportCaseContinuationDraft | null>(null);

  if (!session) {
    return null;
  }

    return (
      <div style={{ display: "grid", gap: 16 }}>
        <SupportCaseWorkbenchSection
          accessToken={session.accessToken}
        onContinueCase={(draft) => setContinuationDraft(draft)}
        onOpenTask={(taskId) => {
          if (typeof window !== "undefined") {
            window.location.hash = `task-${taskId}`;
          }
        }}
        workspaceId={workspaceId}
      />
      <SupportCopilotPanel
        continuationDraft={continuationDraft}
        onContinuationHandled={() => setContinuationDraft(null)}
        workspaceId={workspaceId}
      />
    </div>
  );
}

function JobWorkbench({ workspaceId }: { workspaceId: string }) {
  const { session } = useAuthSession();
  const [continuationDraft, setContinuationDraft] = useState<JobHiringPacketContinuationDraft | null>(null);

  if (!session) {
    return null;
  }

    return (
      <div style={{ display: "grid", gap: 16 }}>
        <JobHiringWorkbenchSection
          accessToken={session.accessToken}
        onContinuePacket={(draft) => setContinuationDraft(draft)}
        onOpenTask={(taskId) => {
          if (typeof window !== "undefined") {
            window.location.hash = `job-task-${taskId}`;
          }
        }}
        workspaceId={workspaceId}
      />
      <JobAssistantActionPanel
        continuationDraft={continuationDraft}
        onContinuationHandled={() => setContinuationDraft(null)}
        workspaceId={workspaceId}
      />
    </div>
  );
}

export default function WorkspaceWorkbenchPanel({
  workspaceId,
  workspaceOverride = null,
}: WorkspaceWorkbenchPanelProps) {
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(workspaceOverride);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadWorkspace = useCallback(async () => {
    if (!session) {
      setWorkspace(null);
      return;
    }

    if (workspaceOverride) {
      setWorkspace(workspaceOverride);
      setErrorMessage(null);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const loadedWorkspace = await getWorkspace(session.accessToken, workspaceId);
      setWorkspace(loadedWorkspace);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载这个工作区。");
    } finally {
      setIsLoading(false);
    }
  }, [session, workspaceId, workspaceOverride]);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  if (!isReady) {
    return <SectionCard title="工作台">正在加载工作区...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="请先登录，再进入工作区工作台。" />;
  }

  if (!workspace) {
    return (
      <SectionCard title="工作台">
        {isLoading ? "正在加载工作区..." : errorMessage ?? "暂时无法读取工作区。"}
      </SectionCard>
    );
  }

  return (
    <div style={{ display: "grid", gap: 18 }}>
      {errorMessage ? (
        <section
          style={{
            backgroundColor: "#fff1f2",
            border: "1px solid #fecdd3",
            borderRadius: 18,
            color: "#b91c1c",
            padding: 16,
          }}
        >
          {errorMessage}
        </section>
      ) : null}

      {workspace.module_type === "research" ? <ResearchWorkbench workspace={workspace} workspaceId={workspaceId} /> : null}
      {workspace.module_type === "support" ? <SupportWorkbench workspaceId={workspaceId} /> : null}
      {workspace.module_type === "job" ? <JobWorkbench workspaceId={workspaceId} /> : null}

      {workspace.module_type !== "research" &&
      workspace.module_type !== "support" &&
      workspace.module_type !== "job" ? (
        <SectionCard title={getModuleDisplayName(workspace.module_type)}>
          当前模块暂时没有可用的工作台布局。
        </SectionCard>
      ) : null}
    </div>
  );
}
