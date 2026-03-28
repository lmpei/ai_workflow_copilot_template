"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  createPublicDemoWorkspaceFromTemplate,
  createWorkspace,
  isApiClientError,
  listPublicDemoTemplates,
  listWorkspaces,
  readPublicDemoSettings,
} from "../../lib/api";
import { clearStoredSession } from "../../lib/auth";
import {
  moduleTypes,
  type ModuleType,
  type PublicDemoSettingsRecord,
  type PublicDemoTemplateRecord,
  type Workspace,
} from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import PublicDemoNotice from "../public-demo/public-demo-notice";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

function getDemoTemplateId(workspace: Workspace): string | null {
  const value = workspace.module_config_json.demo_template_id;
  return typeof value === "string" && value.length > 0 ? value : null;
}

const MODULE_PRODUCT_NAMES: Record<ModuleType, string> = {
  research: "Research Assistant",
  support: "Support Copilot",
  job: "Job Assistant",
};

function getModuleDisplayName(moduleType: ModuleType): string {
  return MODULE_PRODUCT_NAMES[moduleType];
}

export default function WorkspaceManager() {
  const router = useRouter();
  const { session, isReady } = useAuthSession();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [publicDemoSettings, setPublicDemoSettings] = useState<PublicDemoSettingsRecord | null>(null);
  const [demoTemplates, setDemoTemplates] = useState<PublicDemoTemplateRecord[]>([]);
  const [name, setName] = useState("");
  const [moduleType, setModuleType] = useState<ModuleType>("research");
  const [description, setDescription] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [launchingTemplateId, setLaunchingTemplateId] = useState<string | null>(null);

  useEffect(() => {
    const loadPublicDemoContext = async () => {
      try {
        const [settings, templates] = await Promise.all([readPublicDemoSettings(), listPublicDemoTemplates()]);
        setPublicDemoSettings(settings);
        setDemoTemplates(templates);
      } catch {
        setPublicDemoSettings(null);
        setDemoTemplates([]);
      }
    };

    void loadPublicDemoContext();
  }, []);

  useEffect(() => {
    if (!session) {
      setWorkspaces([]);
      return;
    }

    const loadWorkspaces = async () => {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        setWorkspaces(await listWorkspaces(session.accessToken));
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "无法加载工作区");
      } finally {
        setIsLoading(false);
      }
    };

    void loadWorkspaces();
  }, [session]);

  const workspaceLimitReached =
    publicDemoSettings?.public_demo_mode === true &&
    workspaces.length >= publicDemoSettings.max_workspaces_per_user;

  const demoTemplateMap = useMemo(
    () =>
      Object.fromEntries(demoTemplates.map((template) => [template.template_id, template])) as Record<
        string,
        PublicDemoTemplateRecord
      >,
    [demoTemplates],
  );

  const handleCreateWorkspace = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session || workspaceLimitReached) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const workspace = await createWorkspace(session.accessToken, {
        name,
        module_type: moduleType,
        description: description || undefined,
      });
      setWorkspaces((currentWorkspaces) => [workspace, ...currentWorkspaces]);
      setName("");
      setModuleType("research");
      setDescription("");
      router.push(`/workspaces/${workspace.id}`);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法创建工作区");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateGuidedDemo = async (templateId: string) => {
    if (!session || workspaceLimitReached) {
      return;
    }

    setLaunchingTemplateId(templateId);
    setErrorMessage(null);

    try {
      const seededWorkspace = await createPublicDemoWorkspaceFromTemplate(session.accessToken, templateId);
      setWorkspaces((currentWorkspaces) => [seededWorkspace.workspace, ...currentWorkspaces]);
      router.push(`/workspaces/${seededWorkspace.workspace.id}`);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法创建引导演示工作区");
    } finally {
      setLaunchingTemplateId(null);
    }
  };

  const handleLogout = () => {
    clearStoredSession();
    router.push("/login");
  };

  if (!isReady) {
    return <SectionCard title="工作区">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能创建和管理工作区。" />;
  }

  return (
    <>
      <SectionCard title="当前会话" description={`当前登录账号：${session.user.email}。`}>
        <button onClick={handleLogout} type="button">
          退出登录
        </button>
      </SectionCard>

      {publicDemoSettings ? (
        <PublicDemoNotice
          settings={publicDemoSettings}
          description="公网 demo 账号会被明确限制，方便外部用户在没有隐性运维准备的情况下体验系统。"
        />
      ) : null}

      <SectionCard
        title="引导演示工作区"
        description="如果你想快速理解平台，而不是从空白工作区开始，可以直接选择带预置内容的演示路径。"
      >
        {publicDemoSettings?.public_demo_mode ? (
          <p style={{ marginTop: 0 }}>
            当前账号已使用：{workspaces.length} / {publicDemoSettings.max_workspaces_per_user} 个工作区。
          </p>
        ) : null}
        {workspaceLimitReached ? (
          <p style={{ color: "#b45309", marginTop: 0 }}>
            这个公网 demo 账号已达到工作区数量上限。请打开已有工作区，或联系运维重置账号。
          </p>
        ) : null}
        {demoTemplates.length === 0 ? <p>当前暂时没有可用的引导演示模板。</p> : null}
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          }}
        >
          {demoTemplates.map((template) => (
            <div
              key={template.template_id}
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 12,
                padding: 16,
              }}
            >
              <div style={{ alignItems: "center", display: "flex", gap: 8, marginBottom: 8 }}>
                <strong>{template.title}</strong>
                <span
                  style={{
                    backgroundColor: "#0f172a12",
                    borderRadius: 999,
                    color: "#0f172a",
                    fontSize: 12,
                    fontWeight: 600,
                    padding: "2px 10px",
                    textTransform: "uppercase",
                  }}
                >
                  {getModuleDisplayName(template.module_type)}
                </span>
              </div>
              <p style={{ marginTop: 0 }}>{template.summary}</p>
              <p style={{ marginBottom: 8, marginTop: 0 }}>
                <strong>预置文档：</strong> {template.seeded_documents.map((document) => document.title).join("，")}
              </p>
              <p style={{ marginBottom: 12, marginTop: 0 }}>
                <strong>演示路径：</strong> {template.showcase_steps.map((step) => step.title).join(" -> ")}
              </p>
              <button
                disabled={workspaceLimitReached || launchingTemplateId !== null}
                onClick={() => void handleCreateGuidedDemo(template.template_id)}
                type="button"
              >
                {launchingTemplateId === template.template_id ? "正在创建引导演示..." : "创建引导演示"}
              </button>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="创建工作区"
        description="每个工作区都持有自己的文档、对话痕迹、任务、评测和模块工作流状态。"
      >
        <form onSubmit={handleCreateWorkspace} style={{ display: "grid", gap: 12, maxWidth: 520 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>名称</span>
            <input onChange={(event) => setName(event.target.value)} required type="text" value={name} />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>模块</span>
            <select onChange={(event) => setModuleType(event.target.value as ModuleType)} value={moduleType}>
              {moduleTypes.map((value) => (
                <option key={value} value={value}>
                  {getModuleDisplayName(value)}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>说明</span>
            <textarea onChange={(event) => setDescription(event.target.value)} rows={3} value={description} />
          </label>
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button disabled={isSubmitting || workspaceLimitReached} type="submit">
            {isSubmitting ? "正在创建..." : "创建工作区"}
          </button>
        </form>
      </SectionCard>

      <SectionCard title="工作区列表" description="打开工作区后，可以管理文档、grounded chat、场景任务和演示模块页面。">
        {isLoading ? <p>正在加载工作区...</p> : null}
        {!isLoading && workspaces.length === 0 ? <p>还没有工作区。</p> : null}
        <ul>
          {workspaces.map((workspace) => {
            const demoTemplate = demoTemplateMap[getDemoTemplateId(workspace) ?? ""];

            return (
              <li key={workspace.id} style={{ marginBottom: 10 }}>
                <div>
                  <Link href={`/workspaces/${workspace.id}`}>{workspace.name}</Link>
                </div>
                <div>当前模块：{getModuleDisplayName(workspace.module_type)}</div>
                {demoTemplate ? <div>引导演示：{demoTemplate.title}</div> : null}
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                  <Link href={`/workspaces/${workspace.id}/modules`}>模块</Link>
                  <Link href={`/workspaces/${workspace.id}/documents`}>文档</Link>
                  <Link href={`/workspaces/${workspace.id}/chat`}>对话</Link>
                  <Link href={`/workspaces/${workspace.id}/tasks`}>任务</Link>
                  <Link href={`/workspaces/${workspace.id}/analytics`}>分析</Link>
                </div>
              </li>
            );
          })}
        </ul>
      </SectionCard>
    </>
  );
}
