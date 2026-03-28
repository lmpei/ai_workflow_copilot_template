"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getWorkspace, isApiClientError, listScenarioModules } from "../../lib/api";
import { isModuleType } from "../../lib/navigation";
import type { ModuleType, ScenarioModuleRecord, TaskType, Workspace } from "../../lib/types";
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

function getTaskLabel(module: ScenarioModuleRecord, taskType: TaskType): string {
  return module.task_labels[taskType] ?? taskType;
}

function filterTaskTypes(values: unknown, module: ScenarioModuleRecord | null): TaskType[] {
  if (!module || !Array.isArray(values)) {
    return [];
  }

  const supportedTaskTypes = new Set(module.tasks.map((task) => task.task_type));
  return values.filter(
    (value): value is TaskType => typeof value === "string" && supportedTaskTypes.has(value as TaskType),
  );
}

function renderTaskTypeList(module: ScenarioModuleRecord, taskTypes: TaskType[]) {
  return taskTypes.map((taskType) => getTaskLabel(module, taskType)).join(" -> ");
}

export default function ModuleHubPanel({ workspaceId, selectedModuleType }: ModuleHubPanelProps) {
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [scenarioModules, setScenarioModules] = useState<ScenarioModuleRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadWorkspaceContext = useCallback(async () => {
    if (!session) {
      setWorkspace(null);
      setScenarioModules([]);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [loadedWorkspace, loadedScenarioModules] = await Promise.all([
        getWorkspace(session.accessToken, workspaceId),
        listScenarioModules(),
      ]);
      setWorkspace(loadedWorkspace);
      setScenarioModules(loadedScenarioModules);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载工作区模块配置");
    } finally {
      setIsLoading(false);
    }
  }, [session, workspaceId]);

  useEffect(() => {
    void loadWorkspaceContext();
  }, [loadWorkspaceContext]);

  const requestedModule = useMemo(() => {
    if (!selectedModuleType) {
      return null;
    }
    return isModuleType(selectedModuleType) ? selectedModuleType : "invalid";
  }, [selectedModuleType]);

  const scenarioModuleMap = useMemo(
    () =>
      Object.fromEntries(scenarioModules.map((module) => [module.module_type, module])) as Partial<
        Record<ModuleType, ScenarioModuleRecord>
      >,
    [scenarioModules],
  );

  if (!isReady) {
    return <SectionCard title="模块中心">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能查看场景模块入口。" />;
  }

  if (isLoading) {
    return <SectionCard title="模块中心">正在加载工作区模块配置...</SectionCard>;
  }

  if (errorMessage) {
    return (
      <SectionCard title="模块中心" description="模块入口依赖工作区配置。">
        <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p>
      </SectionCard>
    );
  }

  if (requestedModule === "invalid") {
    return (
      <SectionCard title="未找到模块" description="当前路由没有匹配到受支持的场景模块。">
        <p>请从工作区模块中心选择一个受支持的模块。</p>
        <p style={{ marginBottom: 0 }}>
          <Link href={`/workspaces/${workspaceId}/modules`}>返回模块中心</Link>
        </p>
      </SectionCard>
    );
  }

  const activeModuleType = workspace?.module_type ?? "research";
  const activeModule = scenarioModuleMap[activeModuleType] ?? scenarioModules[0] ?? null;

  if (!activeModule) {
    return <SectionCard title="模块中心">当前无法读取场景注册表。</SectionCard>;
  }

  if (requestedModule) {
    const moduleInfo = scenarioModuleMap[requestedModule] ?? activeModule;
    const isActiveModule = moduleInfo.module_type === activeModuleType;
    const configuredTaskTypes = filterTaskTypes(workspace?.module_config_json.entry_task_types, moduleInfo);
    const entryTaskTypes = isActiveModule && configuredTaskTypes.length > 0 ? configuredTaskTypes : moduleInfo.entry_task_types;

    return (
      <SectionCard
        title={moduleInfo.title}
        description={`${moduleInfo.description} 当前工作区仍会共享文档、任务、对话与分析基础面板。`}
      >
        <div style={{ display: "grid", gap: 10 }}>
          <div>
            <strong>工作区：</strong> {workspace?.name ?? workspaceId}
          </div>
          <div>
            <strong>状态：</strong> {isActiveModule ? "当前工作区已启用该模块" : "当前工作区尚未启用该模块"}
          </div>
          <div>
            <strong>入口任务：</strong> {renderTaskTypeList(moduleInfo, entryTaskTypes)}
          </div>
          <div>
            <strong>质量基线：</strong> {moduleInfo.quality_baseline}
          </div>
          <div>
            <strong>评测通过阈值：</strong> {Math.round(moduleInfo.pass_threshold * 100)}%
          </div>
          {isActiveModule ? (
            <>
              <p style={{ margin: 0 }}>
                这个模块已经在当前工作区启用。你可以直接用下面这些共享面板运行任务、查看文档并检查分析信息。
              </p>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <Link href={`/workspaces/${workspaceId}/tasks`}>打开模块任务</Link>
                <Link href={`/workspaces/${workspaceId}/documents`}>查看文档</Link>
                <Link href={`/workspaces/${workspaceId}/chat`}>打开对话</Link>
                <Link href={`/workspaces/${workspaceId}/analytics`}>查看分析</Link>
              </div>
            </>
          ) : (
            <>
              <p style={{ margin: 0 }}>
                当前工作区目前配置的是 <strong>{activeModule.title}</strong>。这里仍然保留该模块的介绍入口，但完整能力会保持受限，直到工作区切换到该模块。
              </p>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <Link href={moduleHref(workspaceId, activeModuleType)}>打开当前激活模块</Link>
                <Link href={`/workspaces/${workspaceId}/modules`}>返回模块中心</Link>
              </div>
            </>
          )}
        </div>
      </SectionCard>
    );
  }

  return (
    <SectionCard title="模块中心" description="从同一个工作区入口了解各模块，再进入共享的任务、文档、对话与分析面板。">
      <p style={{ marginTop: 0 }}>
        <strong>当前工作区模块：</strong> {activeModule.title}
      </p>
      <div
        style={{
          display: "grid",
          gap: 12,
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        }}
      >
        {scenarioModules.map((moduleInfo) => {
          const isActiveModule = moduleInfo.module_type === activeModuleType;

          return (
            <div
              key={moduleInfo.module_type}
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
                  {isActiveModule ? "当前模块" : "可预览"}
                </span>
              </div>
              <p style={{ marginTop: 0 }}>{moduleInfo.description}</p>
              <p style={{ marginTop: 0 }}>
                <strong>入口任务：</strong> {renderTaskTypeList(moduleInfo, moduleInfo.entry_task_types)}
              </p>
              <p style={{ marginTop: 0 }}>
                <strong>质量基线：</strong> {moduleInfo.quality_baseline} / {Math.round(moduleInfo.pass_threshold * 100)}% 通过阈值
              </p>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <Link href={moduleHref(workspaceId, moduleInfo.module_type)}>打开模块</Link>
                {isActiveModule ? <Link href={`/workspaces/${workspaceId}/tasks`}>前往任务页</Link> : null}
              </div>
            </div>
          );
        })}
      </div>
    </SectionCard>
  );
}
