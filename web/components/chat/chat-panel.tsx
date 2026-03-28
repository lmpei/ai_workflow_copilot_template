"use client";

import { useState } from "react";

import { isApiClientError, sendWorkspaceChat } from "../../lib/api";
import type { ChatSource } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type ChatPanelProps = {
  workspaceId: string;
};

type ChatEntry = {
  question: string;
  answer: string;
  traceId: string;
  sources: ChatSource[];
};

export default function ChatPanel({ workspaceId }: ChatPanelProps) {
  const { session, isReady } = useAuthSession();
  const [question, setQuestion] = useState("");
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await sendWorkspaceChat(session.accessToken, workspaceId, {
        question,
      });
      setEntries((currentEntries) => [
        {
          question,
          answer: response.answer,
          traceId: response.trace_id,
          sources: response.sources,
        },
        ...currentEntries,
      ]);
      setQuestion("");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法提交对话请求");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="对话">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能发起工作区对话请求。" />;
  }

  return (
    <>
      <SectionCard title="提问" description={`工作区：${workspaceId}。系统会在可用时优先使用已索引的工作区内容回答。`}>
        <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>问题</span>
            <textarea onChange={(event) => setQuestion(event.target.value)} required rows={4} value={question} />
          </label>
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button disabled={isSubmitting} type="submit">
            {isSubmitting ? "正在提交..." : "发送问题"}
          </button>
        </form>
      </SectionCard>

      <SectionCard title="回答记录" description="每次请求都会返回一个已持久化的 trace 标识符。">
        {entries.length === 0 ? <p>还没有提交过问题。</p> : null}
        <ul>
          {entries.map((entry) => (
            <li key={entry.traceId} style={{ marginBottom: 16 }}>
              <div>
                <strong>问题：</strong> {entry.question}
              </div>
              <div>
                <strong>回答：</strong> {entry.answer}
              </div>
              <div>
                <strong>Trace ID：</strong> {entry.traceId}
              </div>
              <div style={{ marginTop: 8 }}>
                <strong>引用来源：</strong>
                {entry.sources.length === 0 ? (
                  <div>这次没有返回 grounded 引用来源。</div>
                ) : (
                  <ul style={{ marginTop: 8, paddingLeft: 18 }}>
                    {entry.sources.map((source) => (
                      <li key={`${entry.traceId}-${source.chunk_id}`} style={{ marginBottom: 8 }}>
                        <div>
                          <strong>{source.document_title}</strong> - 片段 {source.chunk_index}
                        </div>
                        <div>文档 ID：{source.document_id}</div>
                        <div>片段 ID：{source.chunk_id}</div>
                        <div>{source.snippet}</div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </li>
          ))}
        </ul>
      </SectionCard>
    </>
  );
}
