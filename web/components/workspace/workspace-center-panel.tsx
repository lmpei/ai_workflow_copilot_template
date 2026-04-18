"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import AuthEntryOverlay from "../auth/auth-entry-overlay";
import { useAuthSession } from "../auth/use-auth-session";
import PublicDemoNotice from "../public-demo/public-demo-notice";
import {
  createPublicDemoWorkspaceFromTemplate,
  createWorkspace,
  isApiClientError,
  listPublicDemoTemplates,
  listWorkspaces,
  readPublicDemoSettings,
} from "../../lib/api";
import { clearStoredSession } from "../../lib/auth";
import type {
  ModuleType,
  PublicDemoSettingsRecord,
  PublicDemoTemplateRecord,
  Workspace,
} from "../../lib/types";

const MODULE_PRODUCT_NAMES: Record<ModuleType, string> = {
  research: "AI 热点追踪",
  support: "Support Copilot",
  job: "Job Assistant",
};

const MODULE_NOTES: Record<ModuleType, string> = {
  research: "信号",
  support: "支持",
  job: "招聘",
};

const MODULE_BLURBS: Record<ModuleType, string> = {
  research: "跟进模型、产品、开源与产业变化。",
  support: "围绕固定产品问题生成回应、记录与升级判断。",
  job: "围绕岗位与候选人推进筛选、判断与记录。",
};

const CONCEPT_GROUPS = [
  ["多模态", "推理模型", "长上下文", "工具调用"],
  ["Agent", "Workflow", "MCP", "Memory"],
  ["RAG", "Retrieval", "Tracing", "Observability"],
  ["Evals", "Benchmarks", "Regression", "Guardrails"],
];

function buildDefaultWorkspaceName(moduleType: ModuleType) {
  const prefix: Record<ModuleType, string> = {
    research: "热点追踪",
    support: "产品支持",
    job: "招聘工作",
  };
  const stamp = new Date()
    .toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" })
    .replace(/\//g, ".");
  return `${prefix[moduleType]} ${stamp}`;
}

function buildDefaultDescription(moduleType: ModuleType) {
  const copy: Record<ModuleType, string> = {
    research: "持续跟进最新 AI 热点与关键信号。",
    support: "处理固定产品问题、回应与升级判断。",
    job: "围绕岗位与候选人的持续招聘工作流。",
  };
  return copy[moduleType];
}

function resolveSafeNextPath(candidate: string | null | undefined) {
  if (!candidate) {
    return "/";
  }

  return candidate.startsWith("/") && !candidate.startsWith("//") ? candidate : "/";
}

function buildAuthOverlayHref(nextPath = "/") {
  const safeNextPath = resolveSafeNextPath(nextPath);
  const params = new URLSearchParams({ auth: "1" });
  if (safeNextPath !== "/") {
    params.set("next", safeNextPath);
  }
  return `/?${params.toString()}`;
}

function TopAction({
  href,
  label,
  primary = false,
}: {
  href: string;
  label: string;
  primary?: boolean;
}) {
  return (
    <Link
      href={href}
      style={{
        borderBottom: primary
          ? "2px solid #111827"
          : "1px solid rgba(15,23,42,0.16)",
        color: "#0f172a",
        fontFamily: '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
        fontSize: 14,
        fontWeight: primary ? 700 : 600,
        padding: "8px 0",
        textDecoration: "none",
      }}
    >
      {label}
    </Link>
  );
}

function ModuleEntry({
  disabled,
  isBusy,
  label,
  note,
  onClick,
  teaser,
}: {
  disabled: boolean;
  isBusy: boolean;
  label: string;
  note: string;
  onClick: () => void;
  teaser: string;
}) {
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      style={{
        background: "transparent",
        border: "none",
        color: "#111827",
        cursor: disabled ? "not-allowed" : "pointer",
        display: "grid",
        gap: 20,
        minHeight: 238,
        padding: "32px 42px 28px 0",
        position: "relative",
        textAlign: "left",
      }}
      type="button"
    >
      <span
        style={{
          color: "#64748b",
          fontFamily: '"Consolas", "SFMono-Regular", monospace',
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: "0.16em",
          textTransform: "uppercase",
        }}
      >
        {note}
      </span>

      <div style={{ display: "grid", gap: 12, maxWidth: 320 }}>
        <strong
          style={{
            fontFamily:
              '"Bahnschrift SemiCondensed", "Aptos Display", "Arial Narrow", "Microsoft YaHei UI", sans-serif',
            fontSize: 34,
            fontWeight: 700,
            letterSpacing: "-0.05em",
            lineHeight: 0.96,
          }}
        >
          {label}
        </strong>
        <p
          style={{
            color: "#475569",
            fontFamily:
              '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
            fontSize: 15,
            lineHeight: 1.8,
            margin: 0,
          }}
        >
          {teaser}
        </p>
      </div>

      <div
        style={{
          alignItems: "center",
          borderTop: "1px solid rgba(148,163,184,0.22)",
          display: "flex",
          justifyContent: "flex-end",
          marginTop: "auto",
          paddingTop: 14,
        }}
      >
        <span
          aria-hidden="true"
          style={{
            fontFamily: '"Bahnschrift SemiCondensed", "Arial Narrow", sans-serif',
            fontSize: 22,
            fontWeight: 700,
          }}
        >
          {isBusy ? "↗" : "→"}
        </span>
      </div>
    </button>
  );
}

export default function WorkspaceCenterPanel() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { session, isReady } = useAuthSession();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [publicDemoSettings, setPublicDemoSettings] =
    useState<PublicDemoSettingsRecord | null>(null);
  const [demoTemplates, setDemoTemplates] = useState<PublicDemoTemplateRecord[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [launchingKey, setLaunchingKey] = useState<string | null>(null);

  const authOverlayVisible = !session && searchParams.get("auth") === "1";
  const nextPath = useMemo(
    () => resolveSafeNextPath(searchParams.get("next")),
    [searchParams],
  );

  useEffect(() => {
    const loadPublicDemoContext = async () => {
      try {
        const [settings, templates] = await Promise.all([
          readPublicDemoSettings(),
          listPublicDemoTemplates(),
        ]);
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
        setErrorMessage(
          isApiClientError(error) ? error.message : "无法加载已有工作区。",
        );
      } finally {
        setIsLoading(false);
      }
    };

    void loadWorkspaces();
  }, [session]);

  useEffect(() => {
    if (!session || !authOverlayVisible) {
      return;
    }

    router.replace(nextPath);
  }, [authOverlayVisible, nextPath, router, session]);

  const orderedWorkspaces = useMemo(
    () =>
      [...workspaces].sort(
        (left, right) =>
          new Date(right.updated_at).getTime() -
          new Date(left.updated_at).getTime(),
      ),
    [workspaces],
  );

  const workspaceLimitReached =
    publicDemoSettings?.public_demo_mode === true &&
    orderedWorkspaces.length >= publicDemoSettings.max_workspaces_per_user;

  const researchTemplate =
    demoTemplates.find((template) => template.module_type === "research") ?? null;

  const openAuthOverlay = (targetPath = "/") => {
    router.push(buildAuthOverlayHref(targetPath), { scroll: false });
  };

  const launchWorkspace = async (moduleType: ModuleType) => {
    if (!session) {
      openAuthOverlay(pathname ?? "/");
      return;
    }
    if (workspaceLimitReached) {
      return;
    }

    setLaunchingKey(moduleType);
    setErrorMessage(null);

    try {
      if (moduleType === "research" && researchTemplate) {
        const seededWorkspace = await createPublicDemoWorkspaceFromTemplate(
          session.accessToken,
          researchTemplate.template_id,
        );
        setWorkspaces((current) => [seededWorkspace.workspace, ...current]);
        router.push(`/workspaces/${seededWorkspace.workspace.id}`);
        return;
      }

      const workspace = await createWorkspace(session.accessToken, {
        name: buildDefaultWorkspaceName(moduleType),
        module_type: moduleType,
        description: buildDefaultDescription(moduleType),
      });
      setWorkspaces((current) => [workspace, ...current]);
      router.push(`/workspaces/${workspace.id}`);
    } catch (error) {
      setErrorMessage(
        isApiClientError(error) ? error.message : "无法创建工作区。",
      );
    } finally {
      setLaunchingKey(null);
    }
  };

  const handleLogout = () => {
    clearStoredSession();
    router.push("/");
  };

  if (!isReady) {
    return (
      <div
        style={{
          color: "#475569",
          fontFamily:
            '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
          padding: 24,
        }}
      >
        正在加载产品入口...
      </div>
    );
  }

  return (
    <div style={{ height: "100%", position: "relative" }}>
      <div
        aria-hidden={authOverlayVisible}
        style={{
          display: "grid",
          gap: 12,
          height: "100%",
          opacity: authOverlayVisible ? 0.54 : 1,
          padding: "14px 0 10px",
          pointerEvents: authOverlayVisible ? "none" : "auto",
          transform: authOverlayVisible ? "scale(0.985)" : "scale(1)",
          transition:
            "filter 220ms ease, opacity 220ms ease, transform 220ms ease",
          userSelect: authOverlayVisible ? "none" : "auto",
          filter: authOverlayVisible ? "blur(14px)" : "none",
        }}
      >
        <section
          style={{
            display: "grid",
            gridTemplateRows: "auto 1fr auto",
            height: "100%",
            overflow: "hidden",
            padding: "18px 0 0",
          }}
        >
          <header
            style={{
              alignItems: "center",
              display: "flex",
              flexWrap: "wrap",
              gap: 16,
              justifyContent: "space-between",
            }}
          >
            <span
              style={{
                color: "#0f172a",
                fontFamily:
                  '"Bahnschrift SemiCondensed", "Aptos Display", "Arial Narrow", "Microsoft YaHei UI", sans-serif',
                fontSize: 30,
                fontWeight: 700,
                letterSpacing: "-0.04em",
                lineHeight: 1,
              }}
            >
              LMPAI WEAVE
            </span>

            <div
              style={{
                alignItems: "center",
                display: "flex",
                flexWrap: "wrap",
                gap: 18,
              }}
            >
              {session ? (
                <span
                  style={{
                    color: "#64748b",
                    fontFamily:
                      '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
                    fontSize: 13,
                  }}
                >
                  {session.user.email}
                </span>
              ) : null}
              <TopAction href="https://lmpai.online" label="个人主页" />
              {session ? (
                <>
                  <TopAction href="/workspaces" label="所有工作区" />
                  <TopAction
                    href={
                      orderedWorkspaces[0]
                        ? `/workspaces/${orderedWorkspaces[0].id}`
                        : "/workspaces"
                    }
                    label="继续最近工作"
                    primary
                  />
                  <button
                    onClick={handleLogout}
                    style={{
                      background: "transparent",
                      border: "none",
                      borderBottom: "1px solid rgba(15,23,42,0.16)",
                      color: "#0f172a",
                      cursor: "pointer",
                      fontFamily:
                        '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
                      fontSize: 14,
                      fontWeight: 600,
                      padding: "8px 0",
                    }}
                    type="button"
                  >
                    退出登录
                  </button>
                </>
              ) : (
                <TopAction href={buildAuthOverlayHref("/")} label="进入" primary />
              )}
            </div>
          </header>

          <div
            style={{
              alignItems: "center",
              display: "grid",
              gap: 40,
              gridTemplateColumns: "minmax(0, 1.2fr) minmax(320px, 0.8fr)",
              paddingLeft: 40,
            }}
          >
            <div style={{ display: "grid", gap: 18 }}>
              <h1
                style={{
                  color: "#111827",
                  fontFamily:
                    '"Bahnschrift SemiCondensed", "Aptos Display", "Arial Narrow", "Microsoft YaHei UI", sans-serif',
                  fontSize: "clamp(5rem, 10vw, 9rem)",
                  fontWeight: 700,
                  letterSpacing: "-0.08em",
                  lineHeight: 0.88,
                  margin: 0,
                }}
              >
                缝合怪
              </h1>
            </div>

            <div
              style={{
                alignSelf: "center",
                display: "grid",
                gap: 14,
                maxWidth: 420,
              }}
            >
              {CONCEPT_GROUPS.map((group, index) => (
                <div
                  key={group.join("-")}
                  style={{
                    borderTop:
                      index === 0 ? "none" : "1px solid rgba(148,163,184,0.18)",
                    display: "grid",
                    gap: 6,
                    paddingTop: index === 0 ? 0 : 12,
                  }}
                >
                  <p
                    style={{
                      color: "#0f172a",
                      fontFamily:
                        '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
                      fontSize: 15,
                      lineHeight: 1.8,
                      margin: 0,
                    }}
                  >
                    {group.join(" · ")}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: "grid", gap: 36 }}>
            <section
              aria-label="模块入口"
              style={{
                borderBottom: "1px solid rgba(148,163,184,0.22)",
                borderTop: "1px solid rgba(148,163,184,0.22)",
                display: "grid",
                gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                paddingLeft: 40,
                paddingRight: 18,
                position: "relative",
              }}
            >
              <div
                aria-hidden="true"
                style={{
                  background: "rgba(148,163,184,0.2)",
                  bottom: 28,
                  left: "33.3333%",
                  position: "absolute",
                  top: 150,
                  width: 1,
                }}
              />
              <div
                aria-hidden="true"
                style={{
                  background: "rgba(148,163,184,0.2)",
                  bottom: 28,
                  left: "66.6666%",
                  position: "absolute",
                  top: 150,
                  width: 1,
                }}
              />
              <ModuleEntry
                disabled={workspaceLimitReached || launchingKey !== null}
                isBusy={launchingKey === "research"}
                label={MODULE_PRODUCT_NAMES.research}
                note={MODULE_NOTES.research}
                onClick={() => void launchWorkspace("research")}
                teaser={MODULE_BLURBS.research}
              />
              <ModuleEntry
                disabled={workspaceLimitReached || launchingKey !== null}
                isBusy={launchingKey === "support"}
                label={MODULE_PRODUCT_NAMES.support}
                note={MODULE_NOTES.support}
                onClick={() => void launchWorkspace("support")}
                teaser={MODULE_BLURBS.support}
              />
              <ModuleEntry
                disabled={workspaceLimitReached || launchingKey !== null}
                isBusy={launchingKey === "job"}
                label={MODULE_PRODUCT_NAMES.job}
                note={MODULE_NOTES.job}
                onClick={() => void launchWorkspace("job")}
                teaser={MODULE_BLURBS.job}
              />
            </section>

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <Link
                href="/workspaces"
                style={{
                  color: "#0f172a",
                  fontFamily:
                    '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
                  fontSize: 14,
                  fontWeight: 700,
                  textDecoration: "none",
                }}
              >
                查看全部工作区
              </Link>
            </div>
          </div>
        </section>

        {isLoading ? (
          <div
            style={{
              color: "#64748b",
              fontFamily:
                '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
              fontSize: 13,
            }}
          >
            正在同步工作区信息...
          </div>
        ) : null}

        {errorMessage ? (
          <section
            style={{
              backgroundColor: "#fff1f2",
              border: "1px solid #fecdd3",
              borderRadius: 18,
              color: "#b91c1c",
              fontFamily:
                '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
              padding: 16,
            }}
          >
            {errorMessage}
          </section>
        ) : null}

        {publicDemoSettings?.public_demo_mode ? (
          <details
            style={{
              color: "#64748b",
              fontFamily:
                '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
            }}
          >
            <summary style={{ cursor: "pointer", fontWeight: 700 }}>
              查看 Demo 限制
            </summary>
            <div style={{ marginTop: 12 }}>
              <PublicDemoNotice
                description="这些限制仍然有效。"
                settings={publicDemoSettings}
                variant="compact"
              />
            </div>
          </details>
        ) : null}
      </div>

      {authOverlayVisible ? <AuthEntryOverlay nextPath={nextPath} /> : null}
    </div>
  );
}
