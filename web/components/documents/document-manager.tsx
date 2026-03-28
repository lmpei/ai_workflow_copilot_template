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

function getSourceTypeLabel(sourceType: string): string {
  if (sourceType === "upload") {
    return "上传文件";
  }
  return sourceType;
}

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
        setErrorMessage(isApiClientError(error) ? error.message : "无法加载文档");
      } finally {
        setIsLoading(false);
      }
    };

    void loadDocuments();
  }, [session, workspaceId]);

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
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法重建文档索引");
    } finally {
      setReindexingDocumentId(null);
    }
  };

  const renderStatus = (status: DocumentRecord["status"]) => {
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
          display: "inline-block",
          borderRadius: 999,
          padding: "2px 10px",
          fontSize: 12,
          fontWeight: 600,
          color: style.color,
          backgroundColor: `${style.color}14`,
        }}
      >
        {style.label}
      </span>
    );
  };

  if (!isReady) {
    return <SectionCard title="文档">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能上传和查看工作区文档。" />;
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
