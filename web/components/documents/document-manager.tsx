"use client";

import { useEffect, useMemo, useRef, useState } from "react";

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
  variant?: "full" | "compact";
};

function getSourceTypeLabel(sourceType: string) {
  if (sourceType === "upload") {
    return "上传文件";
  }
  return sourceType;
}

function renderStatus(status: DocumentRecord["status"]) {
  const statusStyles: Record<DocumentRecord["status"], { label: string; color: string }> = {
    uploaded: { label: "已上传", color: "#92400e" },
    parsing: { label: "解析中", color: "#1d4ed8" },
    chunked: { label: "已切片", color: "#0369a1" },
    indexing: { label: "索引中", color: "#7c3aed" },
    indexed: { label: "已索引", color: "#15803d" },
    failed: { label: "失败", color: "#b91c1c" },
  };
  const style = statusStyles[status];

  return (
    <span
      style={{
        backgroundColor: `${style.color}14`,
        borderRadius: 999,
        color: style.color,
        display: "inline-block",
        fontSize: 12,
        fontWeight: 600,
        padding: "2px 10px",
      }}
    >
      {style.label}
    </span>
  );
}

export default function DocumentManager({ workspaceId, variant = "full" }: DocumentManagerProps) {
  const { session, isReady } = useAuthSession();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [reindexingDocumentId, setReindexingDocumentId] = useState<string | null>(null);

  useEffect(() => {
    if (!session) {
      setDocuments([]);
      setSelectedDocumentId(null);
      return;
    }

    const loadDocuments = async () => {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const loadedDocuments = await listWorkspaceDocuments(session.accessToken, workspaceId);
        setDocuments(loadedDocuments);
        setSelectedDocumentId((current) => current ?? loadedDocuments[0]?.id ?? null);
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "无法加载文档");
      } finally {
        setIsLoading(false);
      }
    };

    void loadDocuments();
  }, [session, workspaceId]);

  const selectedDocument = useMemo(
    () => documents.find((document) => document.id === selectedDocumentId) ?? documents[0] ?? null,
    [documents, selectedDocumentId],
  );

  const handleUpload = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session || !selectedFile) {
      setErrorMessage("请先选择要上传的文件。");
      return;
    }

    setIsUploading(true);
    setErrorMessage(null);

    try {
      const uploadedDocument = await uploadWorkspaceDocument(session.accessToken, workspaceId, selectedFile);
      setDocuments((currentDocuments) => [uploadedDocument, ...currentDocuments]);
      setSelectedDocumentId(uploadedDocument.id);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法上传文档");
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
        currentDocuments.map((document) => (document.id === updatedDocument.id ? updatedDocument : document)),
      );
      setSelectedDocumentId(updatedDocument.id);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法重建文档索引");
    } finally {
      setReindexingDocumentId(null);
    }
  };

  if (!isReady) {
    return <SectionCard title="文档">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能上传和查看工作区文档。" />;
  }

  if (variant === "compact") {
    return (
      <SectionCard title="文档" description="这里只保留最需要的文档操作：上传、查看当前文档列表，并在需要时打开一个文档的详情。">
        <div style={{ display: "grid", gap: 18 }}>
          <form onSubmit={handleUpload} style={{ display: "grid", gap: 12 }}>
            <input onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)} ref={fileInputRef} type="file" />
            <div style={{ color: "#475569" }}>需要补材料时，直接上传即可。文档会按当前流程完成 ingest 和索引。</div>
            {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
              <button disabled={isUploading} type="submit">
                {isUploading ? "正在上传..." : "上传文档"}
              </button>
              <span style={{ color: "#475569" }}>当前共 {documents.length} 份文档</span>
            </div>
          </form>

          {isLoading ? <p>正在加载文档...</p> : null}
          {!isLoading && documents.length === 0 ? <p>还没有文档。先上传一份材料，再继续对话或任务。</p> : null}

          {documents.length > 0 ? (
            <div
              style={{
                display: "grid",
                gap: 16,
                gridTemplateColumns: "minmax(240px, 320px) minmax(0, 1fr)",
              }}
            >
              <div style={{ display: "grid", gap: 10 }}>
                {documents.map((document) => {
                  const isActive = selectedDocument?.id === document.id;
                  return (
                    <button
                      key={document.id}
                      onClick={() => setSelectedDocumentId(document.id)}
                      style={{
                        backgroundColor: isActive ? "#eff6ff" : "#ffffff",
                        border: `1px solid ${isActive ? "#60a5fa" : "#cbd5e1"}`,
                        borderRadius: 14,
                        cursor: "pointer",
                        display: "grid",
                        gap: 6,
                        padding: 14,
                        textAlign: "left",
                      }}
                      type="button"
                    >
                      <strong>{document.title}</strong>
                      <div>{renderStatus(document.status)}</div>
                      <div style={{ color: "#475569", fontSize: 13 }}>
                        更新时间：{new Date(document.updated_at).toLocaleString()}
                      </div>
                    </button>
                  );
                })}
              </div>

              {selectedDocument ? (
                <div
                  style={{
                    backgroundColor: "#f8fafc",
                    border: "1px solid #cbd5e1",
                    borderRadius: 16,
                    display: "grid",
                    gap: 10,
                    padding: 16,
                  }}
                >
                  <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10 }}>
                    <strong>{selectedDocument.title}</strong>
                    {renderStatus(selectedDocument.status)}
                  </div>
                  <div>来源类型：{getSourceTypeLabel(selectedDocument.source_type)}</div>
                  <div>MIME 类型：{selectedDocument.mime_type ?? "未知"}</div>
                  <div>更新时间：{new Date(selectedDocument.updated_at).toLocaleString()}</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
                    <button
                      disabled={reindexingDocumentId === selectedDocument.id}
                      onClick={() => void handleReindex(selectedDocument.id)}
                      type="button"
                    >
                      {reindexingDocumentId === selectedDocument.id ? "正在重建索引..." : "重建索引"}
                    </button>
                  </div>
                  <details>
                    <summary>查看技术信息</summary>
                    <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
                      <div>文档 ID：{selectedDocument.id}</div>
                      <div>存储路径：{selectedDocument.file_path ?? "无"}</div>
                    </div>
                  </details>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </SectionCard>
    );
  }

  return (
    <>
      <SectionCard title="上传文档" description="当前上传流程会同步完成 ingest 和索引。">
        <form onSubmit={handleUpload} style={{ display: "grid", gap: 12, maxWidth: 520 }}>
          <input onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)} ref={fileInputRef} type="file" />
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button disabled={isUploading} type="submit">
            {isUploading ? "正在上传..." : "上传文档"}
          </button>
        </form>
      </SectionCard>

      <SectionCard title="文档列表" description={`工作区：${workspaceId}`}>
        {isLoading ? <p>正在加载文档...</p> : null}
        {!isLoading && documents.length === 0 ? <p>还没有上传任何文档。</p> : null}
        <ul>
          {documents.map((document) => (
            <li key={document.id} style={{ marginBottom: 12 }}>
              <div style={{ alignItems: "center", display: "flex", gap: 10, marginBottom: 6 }}>
                <strong>{document.title}</strong>
                {renderStatus(document.status)}
              </div>
              <div>来源类型：{getSourceTypeLabel(document.source_type)}</div>
              <div>MIME 类型：{document.mime_type ?? "未知"}</div>
              <div>存储路径：{document.file_path ?? "无"}</div>
              <div>更新时间：{new Date(document.updated_at).toLocaleString()}</div>
              <button
                disabled={reindexingDocumentId === document.id}
                onClick={() => void handleReindex(document.id)}
                style={{ marginTop: 8 }}
                type="button"
              >
                {reindexingDocumentId === document.id ? "正在重建索引..." : "重建索引"}
              </button>
            </li>
          ))}
        </ul>
      </SectionCard>
    </>
  );
}
