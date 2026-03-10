"use client";

import { useState } from "react";

import { isApiClientError, sendWorkspaceChat } from "../../lib/api";
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
  sourceCount: number;
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
          sourceCount: response.sources.length,
        },
        ...currentEntries,
      ]);
      setQuestion("");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to submit chat request");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Chat">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to run workspace chat requests." />;
  }

  return (
    <>
      <SectionCard title="Ask a question" description={`Workspace: ${workspaceId}`}>
        <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Question</span>
            <textarea
              onChange={(event) => setQuestion(event.target.value)}
              required
              rows={4}
              value={question}
            />
          </label>
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button disabled={isSubmitting} type="submit">
            {isSubmitting ? "Submitting..." : "Send prompt"}
          </button>
        </form>
      </SectionCard>

      <SectionCard title="Responses" description="Each request returns a persisted trace identifier.">
        {entries.length === 0 ? <p>No prompts submitted yet.</p> : null}
        <ul>
          {entries.map((entry) => (
            <li key={entry.traceId} style={{ marginBottom: 16 }}>
              <div>
                <strong>Question:</strong> {entry.question}
              </div>
              <div>
                <strong>Answer:</strong> {entry.answer}
              </div>
              <div>
                <strong>Trace ID:</strong> {entry.traceId}
              </div>
              <div>
                <strong>Sources returned:</strong> {entry.sourceCount}
              </div>
            </li>
          ))}
        </ul>
      </SectionCard>
    </>
  );
}
