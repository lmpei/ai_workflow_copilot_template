"use client";

import { useEffect, useRef, useState } from "react";

import {
  isApiClientError,
  listWorkspaceDocuments,
  reindexDocument,
  uploadWorkspaceDocument,
} from "../../lib/api";
import type { DocumentRecord } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type DocumentManagerProps = {
  workspaceId: string;
};

export default function DocumentManager({ workspaceId }: DocumentManagerProps) {
  const { session, isReady } = useAuthSession();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [reindexingDocumentId, setReindexingDocumentId] = useState<string | null>(null);

  useEffect(() => {
    if (!session) {
      setDocuments([]);
      return;
    }

    const loadDocuments = async () => {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        setDocuments(await listWorkspaceDocuments(session.accessToken, workspaceId));
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to load documents");
      } finally {
        setIsLoading(false);
      }
    };

    void loadDocuments();
  }, [session, workspaceId]);

  const handleUpload = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session || !selectedFile) {
      setErrorMessage("Select a file before uploading.");
      return;
    }

    setIsUploading(true);
    setErrorMessage(null);

    try {
      const uploadedDocument = await uploadWorkspaceDocument(
        session.accessToken,
        workspaceId,
        selectedFile,
      );
      setDocuments((currentDocuments) => [uploadedDocument, ...currentDocuments]);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to upload document");
    } finally {
      setIsUploading(false);
    }
  };

  const handleReindex = async (documentId: string) => {
    if (!session) {
      return;
    }

    setReindexingDocumentId(documentId);
    setErrorMessage(null);

    try {
      const updatedDocument = await reindexDocument(session.accessToken, documentId);
      setDocuments((currentDocuments) =>
        currentDocuments.map((document) =>
          document.id === updatedDocument.id ? updatedDocument : document,
        ),
      );
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to reindex document");
    } finally {
      setReindexingDocumentId(null);
    }
  };

  const renderStatus = (status: DocumentRecord["status"]) => {
    const statusStyles: Record<DocumentRecord["status"], { label: string; color: string }> = {
      uploaded: { label: "uploaded", color: "#92400e" },
      parsing: { label: "parsing", color: "#1d4ed8" },
      chunked: { label: "chunked", color: "#0369a1" },
      indexing: { label: "indexing", color: "#7c3aed" },
      indexed: { label: "indexed", color: "#15803d" },
      failed: { label: "failed", color: "#b91c1c" },
    };
    const style = statusStyles[status];

    return (
      <span
        style={{
          display: "inline-block",
          borderRadius: 999,
          padding: "2px 10px",
          fontSize: 12,
          fontWeight: 600,
          color: style.color,
          backgroundColor: `${style.color}14`,
          textTransform: "uppercase",
        }}
      >
        {style.label}
      </span>
    );
  };

  if (!isReady) {
    return <SectionCard title="Documents">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to upload and inspect workspace documents." />;
  }

  return (
    <>
      <SectionCard
        title="Upload document"
        description="Phase 2 runs synchronous ingest and indexing during upload."
      >
        <form onSubmit={handleUpload} style={{ display: "grid", gap: 12, maxWidth: 520 }}>
          <input
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            ref={fileInputRef}
            type="file"
          />
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button disabled={isUploading} type="submit">
            {isUploading ? "Uploading..." : "Upload document"}
          </button>
        </form>
      </SectionCard>

      <SectionCard title="Document list" description={`Workspace: ${workspaceId}`}>
        {isLoading ? <p>Loading documents...</p> : null}
        {!isLoading && documents.length === 0 ? <p>No documents uploaded yet.</p> : null}
        <ul>
          {documents.map((document) => (
            <li key={document.id} style={{ marginBottom: 12 }}>
              <div style={{ alignItems: "center", display: "flex", gap: 10, marginBottom: 6 }}>
                <strong>{document.title}</strong>
                {renderStatus(document.status)}
              </div>
              <div>Source type: {document.source_type}</div>
              <div>MIME type: {document.mime_type ?? "unknown"}</div>
              <div>Stored path: {document.file_path ?? "n/a"}</div>
              <div>Updated: {new Date(document.updated_at).toLocaleString()}</div>
              <button
                disabled={reindexingDocumentId === document.id}
                onClick={() => void handleReindex(document.id)}
                style={{ marginTop: 8 }}
                type="button"
              >
                {reindexingDocumentId === document.id ? "Reindexing..." : "Reindex"}
              </button>
            </li>
          ))}
        </ul>
      </SectionCard>
    </>
  );
}
