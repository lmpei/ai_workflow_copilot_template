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

const MODULE_PRODUCT_NAMES: Record<string, string> = {
  research: "Research Assistant",
  support: "Support Copilot",
  job: "Job Assistant",
};

function getModuleDisplayName(moduleType: string): string {
  return MODULE_PRODUCT_NAMES[moduleType] ?? moduleType;
}

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
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载引导演示路径");
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
    return <SectionCard title="引导演示路径">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能加载引导演示工作区和演示步骤。" />;
  }

  if (isLoading) {
    return <SectionCard title="引导演示路径">正在加载工作区演示说明...</SectionCard>;
  }

  if (errorMessage) {
    return (
      <SectionCard title="引导演示路径" description="这个工作区演示依赖预置的 public-demo 模板元数据。">
        <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p>
      </SectionCard>
    );
  }

  if (!template || !workspace) {
    return (
      <SectionCard
        title="工作区导览"
        description="这个工作区是手动创建的。请使用下面这些共享页面来添加文档、测试 grounded chat，并运行模块任务。"
      >
        <ol style={{ margin: 0, paddingLeft: 20 }}>
          <li>先打开“文档”页面，为当前模块添加资料。</li>
          <li>再用“对话”页面验证工作区是否能基于已索引语料回答 grounded 问题。</li>
          <li>最后打开“任务”页面，运行模块工作流并查看结构化结果。</li>
        </ol>
      </SectionCard>
    );
  }

  return (
    <SectionCard title={isGuidedDemoWorkspace(workspace) ? "引导演示路径" : "工作区导览"} description={template.summary}>
      <div style={{ display: "grid", gap: 16 }}>
        <div style={{ display: "grid", gap: 6 }}>
          <div>
            <strong>工作区：</strong> {workspace.name}
          </div>
          <div>
            <strong>模块：</strong> {getModuleDisplayName(template.module_type)}
          </div>
          <div>
            <strong>预置文档：</strong> {template.seeded_documents.map((document) => document.title).join("，")}
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
                    <strong>示例提问</strong>
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
                      <strong>建议任务类型：</strong> {step.sample_task_type}
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <strong>建议输入</strong>
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
