"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type MouseEvent, useEffect, useState } from "react";

import { deleteWorkspace, isApiClientError, listWorkspaces } from "../../lib/api";
import type { ModuleType, Workspace } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";

const MODULE_LABELS: Record<ModuleType, string> = {
  research: "AI 热点追踪",
  support: "Support Copilot",
  job: "Job Assistant",
};

function formatWorkspaceTime(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function WorkspaceHistoryRow({
  isDeleting,
  onDelete,
  workspace,
}: {
  isDeleting: boolean;
  onDelete: (workspace: Workspace) => Promise<void>;
  workspace: Workspace;
}) {
  const router = useRouter();
  const [isHovered, setIsHovered] = useState(false);

  const openWorkspace = () => {
    if (isDeleting) {
      return;
    }
    router.push(`/workspaces/${workspace.id}`);
  };

  const handleDelete = async (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    if (isDeleting) {
      return;
    }

    const confirmed = window.confirm(
      `永久删除“${workspace.name}”及其中所有关联数据？此操作不可恢复。`,
    );
    if (!confirmed) {
      return;
    }

    await onDelete(workspace);
  };

  return (
    <article
      onClick={openWorkspace}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openWorkspace();
        }
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      role="button"
      style={{
        alignItems: "center",
        backgroundColor: isHovered ? "rgba(148, 163, 184, 0.12)" : "rgba(255,255,255,0.82)",
        border: "1px solid rgba(148, 163, 184, 0.16)",
        borderRadius: 24,
        color: "#0f172a",
        cursor: isDeleting ? "progress" : "pointer",
        display: "grid",
        gap: 12,
        gridTemplateColumns: "minmax(0, 1fr) auto auto",
        padding: "18px 22px",
        transition: "background-color 160ms ease, border-color 160ms ease",
      }}
      tabIndex={0}
    >
      <div style={{ display: "grid", gap: 6, minWidth: 0 }}>
        <strong
          style={{
            fontSize: 20,
            fontWeight: 800,
            lineHeight: 1.1,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {workspace.name}
        </strong>
        <span style={{ color: "#64748b", fontSize: 13 }}>
          {MODULE_LABELS[workspace.module_type]} · {formatWorkspaceTime(workspace.updated_at)}
        </span>
      </div>

      <span
        style={{
          color: "#64748b",
          fontSize: 12,
          fontWeight: 700,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
        }}
      >
        {workspace.module_type}
      </span>

      <button
        aria-label={`删除工作区 ${workspace.name}`}
        onClick={handleDelete}
        style={{
          alignItems: "center",
          backgroundColor: "transparent",
          border: "none",
          borderRadius: 999,
          color: isDeleting ? "#94a3b8" : "#b91c1c",
          cursor: isDeleting ? "progress" : "pointer",
          display: "inline-flex",
          fontSize: 18,
          height: 36,
          justifyContent: "center",
          width: 36,
        }}
        title="删除工作区"
        type="button"
      >
        🗑
      </button>
    </article>
  );
}

export default function WorkspaceHistoryPage() {
  const { session, isReady } = useAuthSession();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [deletingWorkspaceId, setDeletingWorkspaceId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!session) {
      setWorkspaces([]);
      return;
    }

    let cancelled = false;

    const load = async () => {
      setIsLoading(true);
      setErrorMessage(null);

      try {
        const loaded = await listWorkspaces(session.accessToken);
        if (!cancelled) {
          setWorkspaces(
            [...loaded].sort(
              (left, right) =>
                new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime(),
            ),
          );
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            isApiClientError(error) ? error.message : "暂时无法读取工作区，请稍后再试。",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [session]);

  const handleDeleteWorkspace = async (workspace: Workspace) => {
    if (!session) {
      return;
    }

    setDeletingWorkspaceId(workspace.id);
    setErrorMessage(null);

    try {
      await deleteWorkspace(session.accessToken, workspace.id);
      setWorkspaces((current) => current.filter((item) => item.id !== workspace.id));
    } catch (error) {
      setErrorMessage(
        isApiClientError(error) ? error.message : "删除工作区失败，请稍后再试。",
      );
    } finally {
      setDeletingWorkspaceId(null);
    }
  };

  if (!isReady) {
    return <div style={{ color: "#64748b", padding: 32 }}>正在读取工作区…</div>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能查看和删除你的工作区。" />;
  }

  return (
    <main
      style={{
        background:
          "radial-gradient(circle at 8% 12%, rgba(191, 219, 254, 0.42), transparent 28%), radial-gradient(circle at 88% 10%, rgba(224, 231, 255, 0.34), transparent 24%), #f8fbff",
        minHeight: "100svh",
      }}
    >
      <div
        style={{
          display: "grid",
          gap: 28,
          margin: "0 auto",
          maxWidth: 1120,
          padding: "40px 40px 56px",
        }}
      >
        <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between" }}>
          <div style={{ display: "grid", gap: 8 }}>
            <Link
              href="/"
              style={{
                color: "#64748b",
                fontSize: 14,
                fontWeight: 700,
                textDecoration: "none",
              }}
            >
              返回首页
            </Link>
            <strong
              style={{
                color: "#0f172a",
                fontSize: "clamp(36px, 5vw, 60px)",
                fontWeight: 800,
                letterSpacing: "-0.05em",
                lineHeight: 0.95,
              }}
            >
              所有工作区
            </strong>
          </div>

          <span style={{ color: "#64748b", fontSize: 13 }}>
            {workspaces.length ? `${workspaces.length} 个工作区` : "还没有工作区"}
          </span>
        </div>

        {errorMessage ? (
          <div
            style={{
              backgroundColor: "#fff1f2",
              border: "1px solid #fecdd3",
              borderRadius: 18,
              color: "#b91c1c",
              padding: 16,
            }}
          >
            {errorMessage}
          </div>
        ) : null}

        {isLoading ? (
          <div style={{ color: "#64748b", paddingTop: 24 }}>正在同步工作区…</div>
        ) : workspaces.length ? (
          <section style={{ display: "grid", gap: 14 }}>
            {workspaces.map((workspace) => (
              <WorkspaceHistoryRow
                isDeleting={deletingWorkspaceId === workspace.id}
                key={workspace.id}
                onDelete={handleDeleteWorkspace}
                workspace={workspace}
              />
            ))}
          </section>
        ) : (
          <section
            style={{
              alignItems: "center",
              backgroundColor: "rgba(255,255,255,0.72)",
              border: "1px solid rgba(148, 163, 184, 0.16)",
              borderRadius: 28,
              display: "grid",
              gap: 14,
              justifyItems: "start",
              minHeight: 280,
              padding: "32px 34px",
            }}
          >
            <strong style={{ color: "#0f172a", fontSize: 28, fontWeight: 800 }}>
              还没有工作区
            </strong>
            <p style={{ color: "#475569", lineHeight: 1.8, margin: 0, maxWidth: 420 }}>
              从首页进入任意模块后，新的工作区会自动出现在这里。
            </p>
            <Link
              href="/"
              style={{
                backgroundColor: "#0f172a",
                borderRadius: 999,
                color: "#ffffff",
                fontSize: 14,
                fontWeight: 800,
                padding: "12px 18px",
                textDecoration: "none",
              }}
            >
              返回首页
            </Link>
          </section>
        )}
      </div>
    </main>
  );
}
