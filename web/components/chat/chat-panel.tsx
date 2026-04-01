"use client";

import { useEffect, useMemo, useState } from "react";

import { isApiClientError, sendWorkspaceChat } from "../../lib/api";
import type { ChatSource, ChatToolStep } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type ChatPanelProps = {
  workspaceId: string;
  assistantLabel?: string;
  workflowLabel?: string;
  introTitle?: string;
  introBody?: string;
  placeholder?: string;
  suggestedPrompts?: string[];
  primaryActionLabel?: string;
  outputTitle?: string;
  modes?: Array<{
    value: "rag" | "research_tool_assisted";
    label: string;
    description: string;
  }>;
  onStatusChange?: (status: {
    entryCount: number;
    isSubmitting: boolean;
    currentDraft: string;
    lastTraceId: string | null;
  }) => void;
};

type ChatEntry = {
  question: string;
  answer: string;
  traceId: string;
  mode: "rag" | "research_tool_assisted";
  toolSteps: ChatToolStep[];
  sources: ChatSource[];
};

function PromptCard({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        backgroundColor: active ? "#0f172a" : isHovered ? "#eff6ff" : "#ffffff",
        border: `1px solid ${active ? "#0f172a" : isHovered ? "#60a5fa" : "#cbd5e1"}`,
        borderRadius: 16,
        color: active ? "#f8fafc" : "#0f172a",
        cursor: "pointer",
        display: "grid",
        fontWeight: 700,
        justifyItems: "start",
        minHeight: 60,
        padding: 12,
        textAlign: "left",
        transition: "all 160ms ease",
      }}
      type="button"
    >
      <span style={{ lineHeight: 1.45 }}>{label}</span>
    </button>
  );
}

function AnalysisProgress({ question, phaseIndex }: { question: string; phaseIndex: number }) {
  const phases = ["读取当前资料", "调用分析代理", "整理阶段结论"];

  return (
    <section
      style={{
        backgroundColor: "#eff6ff",
        border: "1px solid #bfdbfe",
        borderRadius: 18,
        display: "grid",
        gap: 12,
        padding: 16,
      }}
    >
      <div style={{ display: "grid", gap: 4 }}>
        <strong style={{ color: "#0f172a", fontSize: 16 }}>分析进行中</strong>
        <p style={{ color: "#334155", lineHeight: 1.7, margin: 0 }}>当前问题：{question}</p>
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        {phases.map((phase, index) => {
          const isCurrent = index === phaseIndex;
          const isDone = index < phaseIndex;
          return (
            <div
              key={phase}
              style={{
                alignItems: "center",
                backgroundColor: "#ffffff",
                border: `1px solid ${isCurrent ? "#60a5fa" : "#dbe4f0"}`,
                borderRadius: 14,
                color: "#0f172a",
                display: "flex",
                gap: 10,
                padding: "10px 12px",
              }}
            >
              <span
                style={{
                  backgroundColor: isDone ? "#15803d" : isCurrent ? "#2563eb" : "#cbd5e1",
                  borderRadius: 999,
                  color: "#ffffff",
                  display: "inline-flex",
                  fontSize: 12,
                  fontWeight: 700,
                  justifyContent: "center",
                  minWidth: 28,
                  padding: "4px 8px",
                }}
              >
                {isDone ? "已完成" : isCurrent ? "进行中" : "等待"}
              </span>
              <span>{phase}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function ChatBubble({ assistantLabel, entry }: { assistantLabel: string; entry: ChatEntry }) {
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <div
          style={{
            backgroundColor: "#0f172a",
            borderRadius: "20px 20px 8px 20px",
            color: "#f8fafc",
            maxWidth: "min(720px, 100%)",
            padding: "16px 18px",
          }}
        >
          <div style={{ color: "#cbd5e1", fontSize: 12, fontWeight: 700, marginBottom: 6 }}>你的问题</div>
          <div style={{ lineHeight: 1.75, whiteSpace: "pre-wrap" }}>{entry.question}</div>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-start" }}>
        <div
          style={{
            backgroundColor: "#ffffff",
            border: "1px solid #dbe4f0",
            borderRadius: "20px 20px 20px 8px",
            boxShadow: "0 18px 40px rgba(15, 23, 42, 0.06)",
            maxWidth: "min(860px, 100%)",
            padding: "18px 20px",
          }}
        >
          <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
            <span
              style={{
                backgroundColor: "#e0f2fe",
                borderRadius: 999,
                color: "#0c4a6e",
                fontSize: 12,
                fontWeight: 700,
                padding: "4px 10px",
              }}
            >
              {assistantLabel}
            </span>
            {entry.mode === "research_tool_assisted" ? (
              <span
                style={{
                  backgroundColor: "#ecfccb",
                  borderRadius: 999,
                  color: "#3f6212",
                  fontSize: 12,
                  fontWeight: 700,
                  padding: "4px 10px",
                }}
              >
                工具辅助试点
              </span>
            ) : null}
            <span style={{ color: "#64748b", fontSize: 12 }}>Trace ID: {entry.traceId}</span>
          </div>
          <div style={{ color: "#1e293b", lineHeight: 1.8, whiteSpace: "pre-wrap" }}>{entry.answer}</div>
          {entry.toolSteps.length > 0 ? (
            <section
              style={{
                backgroundColor: "#f8fafc",
                border: "1px solid #e2e8f0",
                borderRadius: 14,
                display: "grid",
                gap: 10,
                marginTop: 12,
                padding: 12,
              }}
            >
              <strong style={{ color: "#0f172a", fontSize: 14 }}>本轮工具辅助步骤</strong>
              <div style={{ display: "grid", gap: 8 }}>
                {entry.toolSteps.map((step, index) => (
                  <div
                    key={`${entry.traceId}-${step.tool_name}-${index}`}
                    style={{
                      backgroundColor: "#ffffff",
                      border: "1px solid #dbe4f0",
                      borderRadius: 12,
                      display: "grid",
                      gap: 4,
                      padding: 10,
                    }}
                  >
                    <div style={{ color: "#0f172a", fontSize: 13, fontWeight: 700 }}>{step.summary}</div>
                    {step.detail ? <div style={{ color: "#475569", fontSize: 13 }}>{step.detail}</div> : null}
                  </div>
                ))}
              </div>
            </section>
          ) : null}
          <details style={{ marginTop: 12 }}>
            <summary>查看资料引用</summary>
            {entry.sources.length === 0 ? (
              <p style={{ color: "#64748b", marginBottom: 0 }}>这次没有返回可引用的资料来源。</p>
            ) : (
              <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
                {entry.sources.map((source) => (
                  <div
                    key={`${entry.traceId}-${source.chunk_id}`}
                    style={{
                      backgroundColor: "#f8fafc",
                      border: "1px solid #e2e8f0",
                      borderRadius: 14,
                      display: "grid",
                      gap: 6,
                      padding: 12,
                    }}
                  >
                    <strong>{source.document_title}</strong>
                    <div style={{ color: "#475569", fontSize: 13 }}>
                      文档片段 {source.chunk_index} · 文档 ID {source.document_id}
                    </div>
                    <div style={{ color: "#334155", lineHeight: 1.7 }}>{source.snippet}</div>
                  </div>
                ))}
              </div>
            )}
          </details>
        </div>
      </div>
    </div>
  );
}

export default function ChatPanel({
  workspaceId,
  assistantLabel = "Research Assistant",
  workflowLabel = "研究流程",
  introTitle = "从一个研究问题开始",
  introBody = "点一个快捷提示词，或直接输入问题，然后开始分析。",
  placeholder = "例如：请基于当前资料总结最重要的市场信号，并指出还缺哪些证据才能形成正式结论。",
  suggestedPrompts,
  primaryActionLabel = "开始分析",
  outputTitle = "分析过程与结论",
  modes,
  onStatusChange,
}: ChatPanelProps) {
  const { session, isReady } = useAuthSession();
  const [question, setQuestion] = useState("");
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [phaseIndex, setPhaseIndex] = useState(0);
  const availableModes = useMemo(
    () =>
      modes && modes.length > 0
        ? modes
        : [{ value: "rag" as const, label: "普通分析", description: "直接基于当前资料进行 grounded 分析。" }],
    [modes],
  );
  const [mode, setMode] = useState<"rag" | "research_tool_assisted">(availableModes[0]?.value ?? "rag");

  const prompts = useMemo(
    () =>
      suggestedPrompts && suggestedPrompts.length > 0
        ? suggestedPrompts
        : [
            "请先总结当前资料里最重要的研究发现。",
            "请告诉我现在最缺哪些资料，才能继续往下分析。",
            "请判断这批资料里有哪些结论还不够稳，需要进一步核对。",
          ],
    [suggestedPrompts],
  );

  const modeMeta = useMemo(
    () => availableModes.find((candidate) => candidate.value === mode) ?? availableModes[0],
    [availableModes, mode],
  );

  useEffect(() => {
    if (!availableModes.some((candidate) => candidate.value === mode)) {
      setMode(availableModes[0]?.value ?? "rag");
    }
  }, [availableModes, mode]);

  useEffect(() => {
    onStatusChange?.({
      entryCount: entries.length,
      isSubmitting,
      currentDraft: question,
      lastTraceId: entries.at(-1)?.traceId ?? null,
    });
  }, [entries, isSubmitting, onStatusChange, question]);

  useEffect(() => {
    if (!isSubmitting) {
      setPhaseIndex(0);
      return;
    }

    setPhaseIndex(0);
    const timer = window.setInterval(() => {
      setPhaseIndex((current) => (current >= 2 ? current : current + 1));
    }, 900);

    return () => window.clearInterval(timer);
  }, [isSubmitting]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session || !question.trim()) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const trimmedQuestion = question.trim();
      const response = await sendWorkspaceChat(session.accessToken, workspaceId, {
        question: trimmedQuestion,
        mode,
      });
      setEntries((currentEntries) => [
        ...currentEntries,
        {
          question: trimmedQuestion,
          answer: response.answer,
          traceId: response.trace_id,
          mode: response.mode,
          toolSteps: response.tool_steps,
          sources: response.sources,
        },
      ]);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法提交分析请求。");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="研究流程">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能开始研究流程。" />;
  }

  return (
    <section
      style={{
        background: "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,1) 100%)",
        border: "1px solid #dbe4f0",
        borderRadius: 28,
        boxShadow: "0 28px 56px rgba(15, 23, 42, 0.08)",
        display: "grid",
        gap: 16,
        minHeight: 680,
        padding: 20,
      }}
    >
      <section style={{ display: "grid", gap: 10 }}>
        <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
          <span style={{ color: "#0f172a99", fontSize: 12, fontWeight: 700, letterSpacing: "0.14em" }}>{workflowLabel}</span>
          <span style={{ color: "#64748b", fontSize: 13 }}>快捷提示词可点击并插入输入框</span>
        </div>
        {availableModes.length > 1 ? (
          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
              {availableModes.map((candidate) => {
                const active = candidate.value === mode;
                return (
                  <button
                    key={candidate.value}
                    onClick={() => setMode(candidate.value)}
                    style={{
                      backgroundColor: active ? "#0f172a" : "#ffffff",
                      border: `1px solid ${active ? "#0f172a" : "#cbd5e1"}`,
                      borderRadius: 999,
                      color: active ? "#f8fafc" : "#0f172a",
                      fontSize: 13,
                      fontWeight: 700,
                      minHeight: 40,
                      padding: "0 14px",
                    }}
                    type="button"
                  >
                    {candidate.label}
                  </button>
                );
              })}
            </div>
            <div style={{ color: "#475569", fontSize: 14, lineHeight: 1.7 }}>{modeMeta?.description}</div>
          </div>
        ) : null}
        <div style={{ display: "grid", gap: 4 }}>
          <strong style={{ color: "#0f172a", fontSize: 20 }}>{introTitle}</strong>
          <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>{introBody}</p>
        </div>
        <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
          {prompts.map((prompt) => (
            <PromptCard active={question === prompt} key={prompt} label={prompt} onClick={() => setQuestion(prompt)} />
          ))}
        </div>
      </section>

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
        <label style={{ display: "grid", gap: 8 }}>
          <span style={{ color: "#0f172a", fontSize: 14, fontWeight: 800 }}>输入当前问题</span>
          <textarea
            onChange={(event) => setQuestion(event.target.value)}
            placeholder={placeholder}
            required
            rows={5}
            style={{
              borderRadius: 22,
              border: "1px solid #cbd5e1",
              minHeight: 138,
              padding: "18px 20px",
              resize: "vertical",
            }}
            value={question}
          />
        </label>
        {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
        <div style={{ display: "flex", justifyContent: "flex-start" }}>
          <button
            disabled={isSubmitting}
            style={{
              backgroundColor: "#0f172a",
              border: "none",
              borderRadius: 999,
              color: "#ffffff",
              fontSize: 16,
              fontWeight: 800,
              minHeight: 48,
              minWidth: 148,
              padding: "0 22px",
            }}
            type="submit"
          >
            {isSubmitting ? "分析中..." : primaryActionLabel}
          </button>
        </div>
      </form>

      <section
        style={{
          backgroundColor: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: 24,
          display: "grid",
          gap: 14,
          minHeight: 320,
          padding: 18,
        }}
      >
        <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between" }}>
          <strong style={{ color: "#0f172a", fontSize: 18 }}>{outputTitle}</strong>
          <span style={{ color: "#64748b", fontSize: 13 }}>
            {entries.length > 0 ? `已完成 ${entries.length} 次分析` : "尚未开始分析"}
          </span>
        </div>

        {entries.length === 0 && !isSubmitting ? (
          <div
            style={{
              alignItems: "center",
              color: "#64748b",
              display: "grid",
              justifyItems: "start",
              lineHeight: 1.8,
              minHeight: 180,
              padding: 8,
            }}
          >
            开始分析后，这里会持续显示分析进度、assistant 回复、trace 结果与资料引用。
          </div>
        ) : null}

        {isSubmitting ? <AnalysisProgress phaseIndex={phaseIndex} question={question.trim()} /> : null}

        {entries.length > 0 ? (
          <div style={{ display: "grid", gap: 20 }}>
            {entries.map((entry) => (
              <ChatBubble assistantLabel={assistantLabel} entry={entry} key={entry.traceId} />
            ))}
          </div>
        ) : null}
      </section>
    </section>
  );
}
