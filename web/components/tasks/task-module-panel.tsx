"use client";

import { useCallback, useEffect, useState } from "react";

import { getWorkspace, isApiClientError } from "../../lib/api";
import type { Workspace } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import JobAssistantPanel from "../job/job-assistant-panel";
import ResearchAssistantPanel from "../research/research-assistant-panel";
import SupportCopilotPanel from "../support/support-copilot-panel";
import SectionCard from "../ui/section-card";

type TaskModulePanelProps = {
  workspaceId: string;
};

export default function TaskModulePanel({ workspaceId }: TaskModulePanelProps) {
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadWorkspace = useCallback(async () => {
    if (!session) {
      setWorkspace(null);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      setWorkspace(await getWorkspace(session.accessToken, workspaceId));
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to load workspace");
    } finally {
      setIsLoading(false);
    }
  }, [session, workspaceId]);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  if (!isReady) {
    return <SectionCard title="Module Tasks">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to run scenario tasks." />;
  }

  if (isLoading) {
    return <SectionCard title="Module Tasks">Loading workspace module...</SectionCard>;
  }

  if (errorMessage) {
    return (
      <SectionCard title="Module Tasks" description="The task surface depends on workspace module settings.">
        <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p>
      </SectionCard>
    );
  }

  if (workspace?.module_type === "support") {
    return <SupportCopilotPanel workspaceId={workspaceId} />;
  }

  if (workspace?.module_type === "job") {
    return <JobAssistantPanel workspaceId={workspaceId} />;
  }

  if (workspace?.module_type === "research") {
    return <ResearchAssistantPanel workspaceId={workspaceId} />;
  }

  return (
    <SectionCard
      title="Module Tasks"
      description="This task surface will grow module-specific UX as each scenario reaches MVP depth."
    >
      <p>
        The current workspace is configured for <strong>{workspace?.module_type ?? "unknown"}</strong>. A dedicated
        task surface for this module is not available yet.
      </p>
    </SectionCard>
  );
}


