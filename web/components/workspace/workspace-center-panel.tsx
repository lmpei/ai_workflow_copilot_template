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

const MODULE_WORKSPACE_HINTS: Record<ModuleType, string> = {
  research: "适合从资料开始，先补文档，再用对话验证，最后进入任务。",
  support: "如果这是已有问题，进入工作区后直接去任务页里的 Support case 工作台继续。",
  job: "如果这是已有招聘包，进入工作区后直接去任务页里的 Job hiring packet 工作台继续。",
};

function getModuleDisplayName(moduleType: ModuleType): string {
  return MODULE_PRODUCT_NAMES[moduleType];
}

function getWorkspaceContinuationHint(moduleType: ModuleType): string {
  return MODULE_WORKSPACE_HINTS[moduleType];
}

export default function WorkspaceCenterPanel() {
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
  const orderedWorkspaces = useMemo(
    () =>
      [...workspaces].sort(
        (left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime(),
      ),
    [workspaces],
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
      <SectionCard
        title="工作区中心"
        description="先决定你是第一次体验，还是继续已有工作。这里不再要求你同时理解所有页面和平台概念。"
      >
        <div
          style={{
            alignItems: "center",
            display: "flex",
            flexWrap: "wrap",
            gap: 12,
            justifyContent: "space-between",
          }}
        >
          <div>
            <strong>当前账号：</strong> {session.user.email}
          </div>
          <button onClick={handleLogout} type="button">
            退出登录
          </button>
        </div>
        {errorMessage ? <p style={{ color: "#b91c1c", marginBottom: 0 }}>{errorMessage}</p> : null}
      </SectionCard>

      <SectionCard title="建议你先从哪里开始" description="第一次体验和继续已有工作是两条不同路径。先选一条，再进入下一步。">
        <div
          style={{
            display: "grid",
            gap: 16,
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          }}
        >
          <div
            style={{
              border: "1px solid #cbd5e1",
              borderRadius: 16,
              display: "grid",
              gap: 10,
              padding: 18,
            }}
          >
            <strong>第一次体验</strong>
            <div>优先创建一条引导演示工作区。这样你会直接得到预置文档、示例提问和任务输入，不需要自己拼路径。</div>
            <ol style={{ margin: 0, paddingLeft: 20 }}>
              <li>在下面选择一条引导演示</li>
              <li>进入工作区后先看“文档”</li>
              <li>再看“对话”，最后再跑“任务”</li>
            </ol>
          </div>
          <div
            style={{
              border: "1px solid #cbd5e1",
              borderRadius: 16,
              display: "grid",
              gap: 10,
              padding: 18,
            }}
          >
            <strong>继续已有工作</strong>
            <div>如果你已经有工作区，先回到原工作区。Support 和 Job 的已有工作不需要重建，会从已有 case 或 hiring packet 继续。</div>
            <div style={{ color: "#475569" }}>
              当前账号已有 {orderedWorkspaces.length}
              {publicDemoSettings?.public_demo_mode ? ` / ${publicDemoSettings.max_workspaces_per_user}` : ""}
              {" "}个工作区。
            </div>
          </div>
        </div>
      </SectionCard>

      <SectionCard
        title="第一次体验：创建引导演示工作区"
        description="如果你是第一次来，先从这里开始。只有真的需要从空白开始时，再手动创建工作区。"
      >
        {publicDemoSettings?.public_demo_mode ? (
          <p style={{ marginTop: 0 }}>
            当前账号已使用：{orderedWorkspaces.length} / {publicDemoSettings.max_workspaces_per_user} 个工作区。
          </p>
        ) : null}
        {workspaceLimitReached ? (
          <p style={{ color: "#b45309", marginTop: 0 }}>
            这个公网 demo 账号已达到工作区数量上限。请先打开已有工作区，或联系运维重置账号。
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
                borderRadius: 14,
                display: "grid",
                gap: 10,
                padding: 16,
              }}
            >
              <div style={{ alignItems: "center", display: "flex", gap: 8, marginBottom: 4 }}>
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
              <div>{template.summary}</div>
              <div style={{ color: "#475569" }}>创建后按“文档 - 对话 - 任务”的顺序走，就能看懂这条路径。</div>
              <button
                disabled={workspaceLimitReached || launchingTemplateId !== null}
                onClick={() => void handleCreateGuidedDemo(template.template_id)}
                type="button"
              >
                {launchingTemplateId === template.template_id ? "正在创建引导演示..." : "创建引导演示"}
              </button>
              <details>
                <summary>查看预置文档和路径</summary>
                <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
                  <div>
                    <strong>预置文档：</strong> {template.seeded_documents.map((document) => document.title).join("，")}
                  </div>
                  <div>
                    <strong>演示路径：</strong> {template.showcase_steps.map((step) => step.title).join(" -> ")}
                  </div>
                </div>
              </details>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="继续已有工作" description="已有工作区时，先回到原工作区，而不是重新创建一条空白路径。">
        {isLoading ? <p>正在加载工作区...</p> : null}
        {!isLoading && orderedWorkspaces.length === 0 ? <p>当前还没有工作区。第一次体验时，直接从上面的引导演示开始。</p> : null}
        <div style={{ display: "grid", gap: 12 }}>
          {orderedWorkspaces.map((workspace) => {
            const demoTemplate = demoTemplateMap[getDemoTemplateId(workspace) ?? ""];

            return (
              <div
                key={workspace.id}
                style={{
                  border: "1px solid #cbd5e1",
                  borderRadius: 14,
                  display: "grid",
                  gap: 8,
                  padding: 16,
                }}
              >
                <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <strong>{workspace.name}</strong>
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
                    {getModuleDisplayName(workspace.module_type)}
                  </span>
                </div>
                {demoTemplate ? <div>引导演示：{demoTemplate.title}</div> : null}
                <div style={{ color: "#475569" }}>{getWorkspaceContinuationHint(workspace.module_type)}</div>
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                  <Link href={`/workspaces/${workspace.id}`}>打开工作区</Link>
                </div>
              </div>
            );
          })}
        </div>
      </SectionCard>

      <details style={{ marginBottom: 16 }}>
        <summary>查看当前 demo 限制</summary>
        <div style={{ marginTop: 12 }}>
          {publicDemoSettings ? (
            <PublicDemoNotice
              description="这些限制会保留，但不应该压过你的主要起点。先走推荐路径，再在需要时查看这里。"
              settings={publicDemoSettings}
              variant="compact"
            />
          ) : (
            <p>当前没有可展示的 demo 限制信息。</p>
          )}
        </div>
      </details>

      <details>
        <summary>需要从空白开始时，再手动创建工作区</summary>
        <div style={{ marginTop: 12 }}>
          <SectionCard
            title="手动创建工作区"
            description="只有你已经知道自己要做什么，或者不想走引导演示时，才需要从这里开始。"
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
              <div style={{ color: "#475569" }}>{getWorkspaceContinuationHint(moduleType)}</div>
              <button disabled={isSubmitting || workspaceLimitReached} type="submit">
                {isSubmitting ? "正在创建..." : "创建工作区"}
              </button>
            </form>
          </SectionCard>
        </div>
      </details>
    </>
  );
}

