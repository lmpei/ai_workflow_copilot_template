"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getWorkspace, isApiClientError, listPublicDemoTemplates } from "../../lib/api";
import type { PublicDemoTemplateRecord, Workspace } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type GuidedWorkspaceShowcaseProps = {
  workspaceId: string;
};

function getDemoTemplateId(workspace: Workspace | null): string | null {
  const value = workspace?.module_config_json.demo_template_id;
  return typeof value === "string" && value.length > 0 ? value : null;
}

function isGuidedDemoWorkspace(workspace: Workspace | null): boolean {
  return workspace?.module_config_json.guided_demo === true;
}

export default function GuidedWorkspaceShowcase({ workspaceId }: GuidedWorkspaceShowcaseProps) {
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [templates, setTemplates] = useState<PublicDemoTemplateRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadContext = useCallback(async () => {
    if (!session) {
      setWorkspace(null);
      setTemplates([]);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [loadedWorkspace, loadedTemplates] = await Promise.all([
        getWorkspace(session.accessToken, workspaceId),
        listPublicDemoTemplates(),
      ]);
      setWorkspace(loadedWorkspace);
      setTemplates(loadedTemplates);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to load the guided demo path");
    } finally {
      setIsLoading(false);
    }
  }, [session, workspaceId]);

  useEffect(() => {
    void loadContext();
  }, [loadContext]);

  const template = useMemo(() => {
    const templateId = getDemoTemplateId(workspace);
    if (!templateId) {
      return null;
    }
    return templates.find((entry) => entry.template_id === templateId) ?? null;
  }, [templates, workspace]);

  if (!isReady) {
    return <SectionCard title="Guided Demo Path">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to load guided demo workspaces and walkthrough steps." />;
  }

  if (isLoading) {
    return <SectionCard title="Guided Demo Path">Loading workspace walkthrough...</SectionCard>;
  }

  if (errorMessage) {
    return (
      <SectionCard title="Guided Demo Path" description="This workspace walkthrough depends on the seeded public-demo template metadata.">
        <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p>
      </SectionCard>
    );
  }

  if (!template || !workspace) {
    return (
      <SectionCard
        title="Workspace Walkthrough"
        description="This workspace was created manually. Use the shared surfaces below to add documents, test grounded chat, and run module tasks."
      >
        <ol style={{ margin: 0, paddingLeft: 20 }}>
          <li>Open Documents and add source material for the active module.</li>
          <li>Use Chat to verify the workspace can answer grounded questions against the indexed corpus.</li>
          <li>Open Tasks to run the module-specific workflow and inspect the structured result.</li>
        </ol>
      </SectionCard>
    );
  }

  return (
    <SectionCard
      title={isGuidedDemoWorkspace(workspace) ? "Guided Demo Path" : "Workspace Walkthrough"}
      description={template.summary}
    >
      <div style={{ display: "grid", gap: 16 }}>
        <div style={{ display: "grid", gap: 6 }}>
          <div>
            <strong>Workspace:</strong> {workspace.name}
          </div>
          <div>
            <strong>Module:</strong> {template.module_type}
          </div>
          <div>
            <strong>Seeded documents:</strong> {template.seeded_documents.map((document) => document.title).join(", ")}
          </div>
        </div>

        <ol style={{ display: "grid", gap: 16, margin: 0, paddingLeft: 20 }}>
          {template.showcase_steps.map((step) => (
            <li key={step.title}>
              <div style={{ display: "grid", gap: 8 }}>
                <div>
                  <strong>{step.title}</strong>
                </div>
                <div style={{ color: "#475569" }}>{step.description}</div>
                <div>
                  <Link href={`/workspaces/${workspaceId}${step.route_suffix}`}>{step.cta_label}</Link>
                </div>
                {step.sample_prompt ? (
                  <div
                    style={{
                      backgroundColor: "#f8fafc",
                      border: "1px solid #cbd5e1",
                      borderRadius: 12,
                      padding: 12,
                    }}
                  >
                    <strong>Sample prompt</strong>
                    <p style={{ marginBottom: 0, marginTop: 8 }}>{step.sample_prompt}</p>
                  </div>
                ) : null}
                {step.sample_task_type ? (
                  <div
                    style={{
                      backgroundColor: "#f8fafc",
                      border: "1px solid #cbd5e1",
                      borderRadius: 12,
                      padding: 12,
                    }}
                  >
                    <div>
                      <strong>Suggested task type:</strong> {step.sample_task_type}
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <strong>Suggested input</strong>
                      <pre style={{ marginBottom: 0, marginTop: 8, whiteSpace: "pre-wrap" }}>
                        {JSON.stringify(step.sample_task_input, null, 2)}
                      </pre>
                    </div>
                  </div>
                ) : null}
              </div>
            </li>
          ))}
        </ol>
      </div>
    </SectionCard>
  );
}