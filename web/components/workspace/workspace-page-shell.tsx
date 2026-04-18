"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { getWorkspace, isApiClientError } from "../../lib/api";
import { getWorkspacePage, type WorkspacePageId } from "../../lib/navigation";
import type { ModuleType, Workspace } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type WorkspacePageShellProps = {
  workspaceId: string;
  page: WorkspacePageId;
  title: string;
  description: string;
  children: ReactNode;
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

export default function WorkspacePageShell({ workspaceId, page, title, description, children }: WorkspacePageShellProps) {
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
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载工作区信息");
    } finally {
      setIsLoading(false);
    }
  }, [session, workspaceId]);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  const currentPage = getWorkspacePage(page);
  const workspaceName = workspace?.name ?? workspaceId;
  const moduleDisplayName = getModuleDisplayName(workspace?.module_type);

  if (!isReady) {
    return <SectionCard title="工作区">正在加载工作区...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能查看工作区内容。" />;
  }

  return (
    <main style={{ display: "grid", gap: 18 }}>
      <nav aria-label="面包屑" style={{ color: "#475569", display: "flex", flexWrap: "wrap", gap: 8 }}>
        <Link href="/app" style={{ color: "#0f172a", textDecoration: "none" }}>
          项目首页
        </Link>
        <span>/</span>
        <span>{workspaceName}</span>
        <span>/</span>
        <span>{currentPage.label}</span>
      </nav>

      <section
        style={{
          background:
            workspace?.module_type === "research"
              ? "radial-gradient(circle at top right, rgba(8,145,178,0.18), transparent 24%), linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)"
              : "linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%)",
          border: "1px solid #dbe4f0",
          borderRadius: 24,
          display: "grid",
          gap: 12,
          padding: 24,
        }}
      >
        <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10 }}>
          <span
            style={{
              backgroundColor: "#0f172a",
              borderRadius: 999,
              color: "#ffffff",
              fontSize: 12,
              fontWeight: 700,
              padding: "4px 10px",
              textTransform: "uppercase",
            }}
          >
            {currentPage.label}
          </span>
          <span style={{ color: "#475569", fontSize: 14 }}>
            工作区：<strong style={{ color: "#0f172a" }}>{workspaceName}</strong>
          </span>
          <span style={{ color: "#475569", fontSize: 14 }}>
            当前模块：<strong style={{ color: "#0f172a" }}>{moduleDisplayName}</strong>
          </span>
          {isLoading ? <span style={{ color: "#475569", fontSize: 14 }}>正在同步工作区信息...</span> : null}
        </div>
        <div style={{ display: "grid", gap: 6 }}>
          {workspace?.module_type === "research" ? (
            <span
              style={{
                color: "#64748b",
                fontSize: 12,
                fontWeight: 800,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
              }}
            >
              AI Signal Tracker
            </span>
          ) : null}
          <h1 style={{ margin: 0 }}>{title}</h1>
          <p style={{ color: "#334155", margin: 0 }}>{description}</p>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
          <Link href="/app" style={{ color: "#0f172a", textDecoration: "none" }}>
            返回项目首页
          </Link>
          {page !== "workbench" ? (
            <Link href={`/workspaces/${workspaceId}`} style={{ color: "#0f172a", textDecoration: "none" }}>
              返回工作台
            </Link>
          ) : null}
        </div>
        {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
      </section>

      {children}
    </main>
  );
}
