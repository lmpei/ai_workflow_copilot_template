"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getWorkspace, isApiClientError } from "../../lib/api";
import {
  getScenarioModule,
  isModuleType,
  scenarioModules,
  scenarioTaskLabels,
} from "../../lib/navigation";
import type { ModuleType, ScenarioTaskType, Workspace } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type ModuleHubPanelProps = {
  workspaceId: string;
  selectedModuleType?: string;
};

function moduleHref(workspaceId: string, moduleType: ModuleType) {
  return `/workspaces/${workspaceId}/modules/${moduleType}`;
}

function filterScenarioTaskTypes(values: unknown): ScenarioTaskType[] {
  if (!Array.isArray(values)) {
    return [];
  }

  return values.filter(
    (value): value is ScenarioTaskType =>
      typeof value === "string" && value in scenarioTaskLabels,
  );
}

function renderTaskTypeList(taskTypes: ScenarioTaskType[]) {
  return taskTypes.map((taskType) => scenarioTaskLabels[taskType]).join(" · ");
}

export default function ModuleHubPanel({
  workspaceId,
  selectedModuleType,
}: ModuleHubPanelProps) {
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

  const requestedModule = useMemo(() => {
    if (!selectedModuleType) {
      return null;
    }
    return isModuleType(selectedModuleType) ? selectedModuleType : "invalid";
  }, [selectedModuleType]);

  if (!isReady) {
    return <SectionCard title="Scenario Modules">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to browse scenario module entry points." />;
  }

  if (isLoading) {
    return <SectionCard title="Scenario Modules">Loading workspace module settings...</SectionCard>;
  }

  if (errorMessage) {
    return (
      <SectionCard
        title="Scenario Modules"
        description="Module entry points depend on workspace configuration."
      >
        <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p>
      </SectionCard>
    );
  }

  if (requestedModule === "invalid") {
    return (
      <SectionCard
        title="Module Not Found"
        description="This route does not match a supported scenario module."
      >
        <p>Choose one of the supported modules from the workspace module hub.</p>
        <p style={{ marginBottom: 0 }}>
          <Link href={`/workspaces/${workspaceId}/modules`}>Back to module hub</Link>
        </p>
      </SectionCard>
    );
  }

  const activeModuleType = workspace?.module_type ?? "research";
  const activeModule = getScenarioModule(activeModuleType);

  if (requestedModule) {
    const moduleInfo = getScenarioModule(requestedModule);
    const isActiveModule = moduleInfo.moduleType === activeModuleType;
    const configuredTaskTypes = filterScenarioTaskTypes(workspace?.module_config_json.entry_task_types);
    const entryTaskTypes = isActiveModule && configuredTaskTypes.length > 0
      ? configuredTaskTypes
      : moduleInfo.entryTaskTypes;

    return (
      <SectionCard
        title={moduleInfo.title}
        description={`${moduleInfo.description} Workspace scope remains shared across documents, tasks, chat, and analytics.`}
      >
        <div style={{ display: "grid", gap: 10 }}>
          <div>
            <strong>Workspace:</strong> {workspace?.name ?? workspaceId}
          </div>
          <div>
            <strong>Status:</strong> {isActiveModule ? "active in this workspace" : "not configured for this workspace"}
          </div>
          <div>
            <strong>Entry tasks:</strong> {renderTaskTypeList(entryTaskTypes)}
          </div>
          {isActiveModule ? (
            <>
              <p style={{ margin: 0 }}>
                This module is active here. Use the shared workspace surfaces below to run tasks, inspect documents,
                and review analytics without leaving workspace scope.
              </p>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <Link href={`/workspaces/${workspaceId}/tasks`}>Open module tasks</Link>
                <Link href={`/workspaces/${workspaceId}/documents`}>Review documents</Link>
                <Link href={`/workspaces/${workspaceId}/chat`}>Open chat</Link>
                <Link href={`/workspaces/${workspaceId}/analytics`}>Inspect analytics</Link>
              </div>
            </>
          ) : (
            <>
              <p style={{ margin: 0 }}>
                This workspace is currently configured for <strong>{activeModule.title}</strong>. We keep this module
                discoverable here, but its full surface stays gated until the workspace is configured for it.
              </p>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <Link href={moduleHref(workspaceId, activeModuleType)}>Open active module</Link>
                <Link href={`/workspaces/${workspaceId}/modules`}>Back to module hub</Link>
              </div>
            </>
          )}
        </div>
      </SectionCard>
    );
  }

  return (
    <SectionCard
      title="Scenario Modules"
      description="Discover each module from one shared workspace entry point, then move into the existing tasks, docs, chat, and analytics surfaces."
    >
      <p style={{ marginTop: 0 }}>
        <strong>Active workspace module:</strong> {activeModule.title}
      </p>
      <div
        style={{
          display: "grid",
          gap: 12,
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        }}
      >
        {scenarioModules.map((moduleInfo) => {
          const isActiveModule = moduleInfo.moduleType === activeModuleType;

          return (
            <div
              key={moduleInfo.moduleType}
              style={{
                border: isActiveModule ? "1px solid #0f172a" : "1px solid #cbd5e1",
                borderRadius: 12,
                padding: 14,
              }}
            >
              <div style={{ alignItems: "center", display: "flex", gap: 8, marginBottom: 8 }}>
                <strong>{moduleInfo.title}</strong>
                <span
                  style={{
                    backgroundColor: isActiveModule ? "#0f172a12" : "#64748b12",
                    borderRadius: 999,
                    color: isActiveModule ? "#0f172a" : "#475569",
                    fontSize: 12,
                    fontWeight: 600,
                    padding: "2px 10px",
                    textTransform: "uppercase",
                  }}
                >
                  {isActiveModule ? "active" : "preview"}
                </span>
              </div>
              <p style={{ marginTop: 0 }}>{moduleInfo.description}</p>
              <p style={{ marginTop: 0 }}>
                <strong>Entry tasks:</strong> {renderTaskTypeList(moduleInfo.entryTaskTypes)}
              </p>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <Link href={moduleHref(workspaceId, moduleInfo.moduleType)}>Open module</Link>
                {isActiveModule ? <Link href={`/workspaces/${workspaceId}/tasks`}>Go to tasks</Link> : null}
              </div>
            </div>
          );
        })}
      </div>
    </SectionCard>
  );
}


