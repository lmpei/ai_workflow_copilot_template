"use client";

import type { CSSProperties } from "react";
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
import { useAuthSession } from "../auth/use-auth-session";
import PublicDemoNotice from "../public-demo/public-demo-notice";
import SectionCard from "../ui/section-card";

const MODULE_PRODUCT_NAMES: Record<ModuleType, string> = {
  research: "Research Assistant",
  support: "Support Copilot",
  job: "Job Assistant",
};

const shellCardStyle: CSSProperties = {
  background: "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,1) 100%)",
  border: "1px solid #dbe4f0",
  borderRadius: 28,
  boxShadow: "0 24px 48px rgba(15, 23, 42, 0.08)",
};

const pillLinkStyle: CSSProperties = {
  alignItems: "center",
  borderRadius: 999,
  display: "inline-flex",
  fontWeight: 700,
  justifyContent: "center",
  minHeight: 42,
  padding: "0 16px",
  textDecoration: "none",
};

const actionButtonStyle: CSSProperties = {
  alignItems: "center",
  borderRadius: 999,
  display: "inline-flex",
  fontWeight: 700,
  justifyContent: "center",
  minHeight: 42,
  padding: "0 16px",
};

function getModuleDisplayName(moduleType: ModuleType): string {
  return MODULE_PRODUCT_NAMES[moduleType];
}

function formatDateTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    month: "2-digit",
    day: "2-digit",
  });
}

function WorkspaceCard({ workspace }: { workspace: Workspace }) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <Link
      href={`/workspaces/${workspace.id}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        alignItems: "center",
        backgroundColor: isHovered ? "#eff6ff" : "#ffffff",
        border: `1px solid ${isHovered ? "#60a5fa" : "#dbe4f0"}`,
        borderRadius: 16,
        color: "#0f172a",
        display: "grid",
        gap: 4,
        padding: 14,
        textDecoration: "none",
        transition: "all 160ms ease",
      }}
    >
      <div style={{ alignItems: "center", display: "flex", gap: 8, justifyContent: "space-between" }}>
        <strong style={{ fontSize: 15, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {workspace.name}
        </strong>
        <span
          style={{
            backgroundColor: isHovered ? "#dbeafe" : "#f1f5f9",
            borderRadius: 999,
            color: "#334155",
            display: "inline-flex",
            fontSize: 11,
            fontWeight: 700,
            padding: "4px 8px",
            whiteSpace: "nowrap",
          }}
        >
          {getModuleDisplayName(workspace.module_type)}
        </span>
      </div>
      <div style={{ color: "#64748b", fontSize: 12 }}>最近更新：{formatDateTime(workspace.updated_at)}</div>
    </Link>
  );
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
        setErrorMessage(isApiClientError(error) ? error.message : "无法加载已有工作区。");
      } finally {
        setIsLoading(false);
      }
    };

    void loadWorkspaces();
  }, [session]);

  const orderedWorkspaces = useMemo(
    () => [...workspaces].sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime()),
    [workspaces],
  );

  const workspaceLimitReached =
    publicDemoSettings?.public_demo_mode === true &&
    orderedWorkspaces.length >= publicDemoSettings.max_workspaces_per_user;

  const handleCreateGuidedDemo = async (templateId: string) => {
    if (!session) {
      router.push("/login");
      return;
    }

    if (workspaceLimitReached) {
      return;
    }

    setLaunchingTemplateId(templateId);
    setErrorMessage(null);

    try {
      const seededWorkspace = await createPublicDemoWorkspaceFromTemplate(session.accessToken, templateId);
      setWorkspaces((currentWorkspaces) => [seededWorkspace.workspace, ...currentWorkspaces]);
      router.push(`/workspaces/${seededWorkspace.workspace.id}`);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法创建引导演示工作区。");
    } finally {
      setLaunchingTemplateId(null);
    }
  };

  const handleCreateWorkspace = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session) {
      router.push("/login");
      return;
    }

    if (workspaceLimitReached) {
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
      setErrorMessage(isApiClientError(error) ? error.message : "无法创建工作区。");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = () => {
    clearStoredSession();
    router.push("/app");
  };

  if (!isReady) {
    return <SectionCard title="项目主页">正在加载项目入口...</SectionCard>;
  }

  return (
    <div style={{ display: "grid", gap: 14 }}>
      <section
        style={{
          ...shellCardStyle,
          display: "grid",
          gap: 12,
          padding: 22,
        }}
      >
        <div style={{ alignItems: "start", display: "grid", gap: 12, gridTemplateColumns: "minmax(0, 1fr) auto" }}>
          <div style={{ display: "grid", gap: 6 }}>
            <div style={{ color: "#0f172a99", fontSize: 12, fontWeight: 700, letterSpacing: "0.16em" }}>PROJECT</div>
            <h1 style={{ color: "#0f172a", fontSize: "clamp(2rem, 3.5vw, 2.8rem)", lineHeight: 1.02, margin: 0 }}>LMPAI Loom</h1>
            <p style={{ color: "#475569", lineHeight: 1.65, margin: 0, maxWidth: 680 }}>
              围绕资料接入、分析过程和正式输出组织起来的 AI 研究工作流。
            </p>
          </div>

          <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10, justifyContent: "flex-end" }}>
            <Link
              href="/"
              style={{
                ...pillLinkStyle,
                backgroundColor: "#ffffff",
                border: "1px solid #cbd5e1",
                color: "#0f172a",
              }}
            >
              返回个人主页
            </Link>
            {session ? (
              <>
                <span style={{ color: "#475569", fontSize: 14 }}>{session.user.email}</span>
                <button
                  onClick={handleLogout}
                  style={{
                    ...actionButtonStyle,
                    backgroundColor: "#0f172a",
                    border: "none",
                    color: "#ffffff",
                  }}
                  type="button"
                >
                  退出登录
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  style={{
                    ...pillLinkStyle,
                    backgroundColor: "#0f172a",
                    color: "#ffffff",
                  }}
                >
                  登录
                </Link>
                <Link
                  href="/register"
                  style={{
                    ...pillLinkStyle,
                    backgroundColor: "#ffffff",
                    border: "1px solid #cbd5e1",
                    color: "#0f172a",
                  }}
                >
                  注册
                </Link>
              </>
            )}
          </div>
        </div>

        {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
      </section>

      <section
        style={{
          ...shellCardStyle,
          alignItems: "center",
          display: "grid",
          gap: 10,
          gridTemplateColumns: "auto minmax(0, 1fr)",
          padding: "14px 18px",
        }}
      >
        <strong style={{ color: "#0f172a", fontSize: 15 }}>第一次体验</strong>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          {demoTemplates.length === 0 ? <span style={{ color: "#64748b" }}>当前没有可用演示。</span> : null}
          {demoTemplates.map((template) => (
            <button
              key={template.template_id}
              disabled={workspaceLimitReached || launchingTemplateId !== null}
              onClick={() => void handleCreateGuidedDemo(template.template_id)}
              style={{
                alignItems: "center",
                background: launchingTemplateId === template.template_id
                  ? "linear-gradient(135deg, #1d4ed8 0%, #0f172a 100%)"
                  : "linear-gradient(135deg, #0f172a 0%, #2563eb 100%)",
                border: "none",
                borderRadius: 999,
                boxShadow: "0 12px 24px rgba(37, 99, 235, 0.18)",
                color: "#ffffff",
                cursor: "pointer",
                display: "inline-flex",
                fontWeight: 700,
                gap: 10,
                minHeight: 40,
                padding: "0 16px",
              }}
              type="button"
            >
              <span>{launchingTemplateId === template.template_id ? "正在创建..." : template.title}</span>
              <span style={{ color: "rgba(255,255,255,0.74)", fontSize: 12 }}>{getModuleDisplayName(template.module_type)}</span>
            </button>
          ))}
        </div>
      </section>

      <div
        style={{
          alignItems: "start",
          display: "grid",
          gap: 14,
          gridTemplateColumns: "minmax(320px, 0.9fr) minmax(0, 1.1fr)",
        }}
      >
        <SectionCard title="手动创建空白工作区">
          {session ? (
            <form onSubmit={handleCreateWorkspace} style={{ display: "grid", gap: 12 }}>
              <label style={{ display: "grid", gap: 6 }}>
                <span>工作区名称</span>
                <input onChange={(event) => setName(event.target.value)} required type="text" value={name} />
              </label>
              <label style={{ display: "grid", gap: 6 }}>
                <span>模块类型</span>
                <select onChange={(event) => setModuleType(event.target.value as ModuleType)} value={moduleType}>
                  {moduleTypes.map((value) => (
                    <option key={value} value={value}>
                      {getModuleDisplayName(value)}
                    </option>
                  ))}
                </select>
              </label>
              <label style={{ display: "grid", gap: 6 }}>
                <span>一句话说明</span>
                <textarea
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="例如：围绕竞争产品资料梳理市场机会。"
                  rows={3}
                  value={description}
                />
              </label>
              <button disabled={isSubmitting || workspaceLimitReached} type="submit">
                {isSubmitting ? "正在创建..." : "创建工作区"}
              </button>
            </form>
          ) : (
            <div style={{ display: "grid", gap: 12 }}>
              <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>
                登录后即可创建自己的工作区，或先从上面的引导演示开始体验。
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                <Link
                  href="/login"
                  style={{
                    ...pillLinkStyle,
                    backgroundColor: "#0f172a",
                    color: "#ffffff",
                  }}
                >
                  登录后创建
                </Link>
                <Link
                  href="/register"
                  style={{
                    ...pillLinkStyle,
                    backgroundColor: "#ffffff",
                    border: "1px solid #cbd5e1",
                    color: "#0f172a",
                  }}
                >
                  注册账号
                </Link>
              </div>
            </div>
          )}
        </SectionCard>

        <SectionCard title="历史工作区">
          {!session ? <p style={{ margin: 0 }}>登录后可以看到最近的工作区。</p> : null}
          {session && isLoading ? <p style={{ margin: 0 }}>正在同步工作区...</p> : null}
          {session && !isLoading && orderedWorkspaces.length === 0 ? (
            <p style={{ margin: 0 }}>还没有工作区。先从上面的演示或左侧空白创建开始。</p>
          ) : null}
          <div
            style={{
              border: "1px solid #dbe4f0",
              borderRadius: 18,
              display: "grid",
              gap: 8,
              maxHeight: 320,
              overflowY: "auto",
              padding: 8,
            }}
          >
            {session ? orderedWorkspaces.map((workspace) => <WorkspaceCard key={workspace.id} workspace={workspace} />) : null}
          </div>
        </SectionCard>
      </div>

      {publicDemoSettings?.public_demo_mode ? (
        <details>
          <summary>查看当前 demo 限制</summary>
          <div style={{ marginTop: 12 }}>
            <PublicDemoNotice description="这些限制仍然有效，但不应该盖过主要入口。" settings={publicDemoSettings} variant="compact" />
          </div>
        </details>
      ) : null}
    </div>
  );
}
