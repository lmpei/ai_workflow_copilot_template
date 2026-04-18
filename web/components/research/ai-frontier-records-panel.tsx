"use client";

import { useEffect, useState } from "react";

import { isApiClientError, listWorkspaceAiFrontierResearchRecords } from "../../lib/api";
import type { AiFrontierResearchRecord } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import AiFrontierOutputCard from "./ai-frontier-output-card";

type AiFrontierRecordsPanelProps = {
  workspaceId: string;
};

function formatDateTime(value: string) {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime())
    ? value
    : parsed.toLocaleString("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
}

export default function AiFrontierRecordsPanel({ workspaceId }: AiFrontierRecordsPanelProps) {
  const { session, isReady } = useAuthSession();
  const [records, setRecords] = useState<AiFrontierResearchRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!session) {
      setRecords([]);
      return;
    }

    let cancelled = false;
    const load = async () => {
      setIsLoading(true);
      setErrorMessage(null);

      try {
        const items = await listWorkspaceAiFrontierResearchRecords(session.accessToken, workspaceId, 8);
        if (!cancelled) {
          setRecords(items);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(isApiClientError(error) ? error.message : "无法加载热点追踪记录。");
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
  }, [session, workspaceId]);

  if (!isReady) {
    return null;
  }

  if (!session) {
    return <AuthRequired description="登录后才能查看热点追踪记录。" />;
  }

  return (
    <section
      style={{
        display: "grid",
        gap: 16,
      }}
    >
      <div style={{ display: "grid", gap: 6 }}>
        <span
          style={{
            color: "#64748b",
            fontSize: 12,
            fontWeight: 800,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
          }}
        >
          Recent Records
        </span>
        <div style={{ alignItems: "baseline", display: "flex", justifyContent: "space-between", gap: 10 }}>
          <strong style={{ color: "#0f172a", fontSize: 20 }}>最近追踪记录</strong>
          {records.length ? <span style={{ color: "#64748b", fontSize: 13 }}>共 {records.length} 条</span> : null}
        </div>
      </div>

      {isLoading ? (
        <div
          style={{
            backgroundColor: "#ffffff",
            border: "1px solid #dbe4f0",
            borderRadius: 20,
            color: "#475569",
            padding: 18,
          }}
        >
          正在加载最近记录...
        </div>
      ) : null}

      {errorMessage ? (
        <div
          style={{
            backgroundColor: "#fff1f2",
            border: "1px solid #fecdd3",
            borderRadius: 20,
            color: "#b91c1c",
            padding: 18,
          }}
        >
          {errorMessage}
        </div>
      ) : null}

      {!isLoading && !errorMessage && records.length === 0 ? (
        <div
          style={{
            backgroundColor: "#ffffff",
            border: "1px solid #dbe4f0",
            borderRadius: 20,
            color: "#475569",
            lineHeight: 1.8,
            padding: 18,
          }}
        >
          当前还没有沉淀出的热点追踪记录。完成一次追踪后，这里会自动保留最近结果。
        </div>
      ) : null}

      {!isLoading && !errorMessage
        ? records.map((record) => (
            <article
              key={record.id}
              style={{
                backgroundColor: "#ffffff",
                border: "1px solid #dbe4f0",
                borderRadius: 22,
                display: "grid",
                gap: 14,
                padding: 18,
              }}
            >
              <div style={{ display: "grid", gap: 6 }}>
                <strong style={{ color: "#0f172a", fontSize: 17 }}>{record.title}</strong>
                <p style={{ color: "#334155", lineHeight: 1.8, margin: 0 }}>{record.question}</p>
                <span style={{ color: "#64748b", fontSize: 13 }}>{formatDateTime(record.created_at)}</span>
              </div>
              <AiFrontierOutputCard output={record.output} title="本条记录输出" />
            </article>
          ))
        : null}
    </section>
  );
}
