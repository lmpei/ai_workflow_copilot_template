"use client";

import type { CSSProperties, ChangeEvent, DragEvent } from "react";
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
  variant?: "full" | "compact" | "dock";
  onOpenLibrary?: () => void;
  onStatusChange?: (status: {
    totalCount: number;
    readyCount: number;
    hasFailed: boolean;
    latestDocumentTitle: string | null;
  }) => void;
};

const uploadZoneBaseStyle: CSSProperties = {
  alignItems: "center",
  backgroundColor: "#f8fafc",
  border: "1px dashed #94a3b8",
  borderRadius: 16,
  cursor: "pointer",
  display: "grid",
  gap: 6,
  justifyItems: "start",
  padding: 16,
  transition: "all 160ms ease",
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
    indexed: { label: "已就绪", color: "#15803d" },
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
        fontWeight: 700,
        padding: "2px 10px",
      }}
    >
      {style.label}
    </span>
  );
}

export default function DocumentManager({
  workspaceId,
  variant = "full",
  onOpenLibrary,
  onStatusChange,
}: DocumentManagerProps) {
  const { session, isReady } = useAuthSession();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [reindexingDocumentId, setReindexingDocumentId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

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
        setErrorMessage(isApiClientError(error) ? error.message : "无法加载资料。");
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

  useEffect(() => {
    onStatusChange?.({
      totalCount: documents.length,
      readyCount: documents.filter((document) => document.status === "indexed").length,
      hasFailed: documents.some((document) => document.status === "failed"),
      latestDocumentTitle: selectedDocument?.title ?? documents[0]?.title ?? null,
    });
  }, [documents, onStatusChange, selectedDocument]);

  const setPickedFile = (file: File | null) => {
    setSelectedFile(file);
    if (file) {
      setErrorMessage(null);
    }
  };

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    setPickedFile(event.target.files?.[0] ?? null);
  };

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0] ?? null;
    setPickedFile(file);
  };

  const handleUpload = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session || !selectedFile) {
      setErrorMessage("请先拖入文件或点击选择文件。");
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
      setErrorMessage(isApiClientError(error) ? error.message : "无法上传资料。");
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
      setErrorMessage(isApiClientError(error) ? error.message : "无法重建资料索引。");
    } finally {
      setReindexingDocumentId(null);
    }
  };

  const uploadZone = (
    <>
      <input hidden onChange={handleInputChange} ref={fileInputRef} type="file" />
      <div
        onClick={openFilePicker}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        role="button"
        style={{
          ...uploadZoneBaseStyle,
          backgroundColor: isDragging ? "#eff6ff" : "#f8fafc",
          borderColor: isDragging ? "#60a5fa" : "#94a3b8",
        }}
        tabIndex={0}
      >
        <strong style={{ color: "#0f172a" }}>拖动文件到这里，或点击选择文件</strong>
        <div style={{ color: "#475569", fontSize: 13, lineHeight: 1.7 }}>支持拖拽上传，也支持通过文件选择器导入。</div>
        {selectedFile ? <div style={{ color: "#0f172a", fontSize: 13 }}>待上传：{selectedFile.name}</div> : null}
      </div>
    </>
  );

  if (!isReady) {
    return <SectionCard title="资料">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能上传和查看工作区资料。" />;
  }

  if (variant === "dock") {
    return (
      <section
        style={{
          backgroundColor: "#ffffff",
          border: "1px solid #dbe4f0",
          borderRadius: 20,
          display: "grid",
          gap: 12,
          padding: 16,
        }}
      >
        <div style={{ display: "grid", gap: 6 }}>
          <div style={{ color: "#64748b", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>资料上下文</div>
          <strong style={{ color: "#0f172a", fontSize: 17 }}>当前已接入 {documents.length} 份资料</strong>
          <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>
            默认不展开资料列表。先拖入或选择文件，需要详细检查时再打开资料库。
          </p>
        </div>

        <form onSubmit={handleUpload} style={{ display: "grid", gap: 10 }}>
          {uploadZone}
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            <button
              disabled={isUploading}
              style={{ borderRadius: 999, fontWeight: 700, minHeight: 38, padding: "0 14px" }}
              type="submit"
            >
              {isUploading ? "正在上传..." : "上传资料"}
            </button>
            <button onClick={openFilePicker} style={{ borderRadius: 999, minHeight: 38, padding: "0 14px" }} type="button">
              选择文件
            </button>
            {onOpenLibrary ? (
              <button
                onClick={onOpenLibrary}
                style={{ borderRadius: 999, minHeight: 38, padding: "0 14px" }}
                type="button"
              >
                打开资料库
              </button>
            ) : null}
          </div>
        </form>

        {isLoading ? <p style={{ color: "#64748b", margin: 0 }}>正在同步资料...</p> : null}
        {!isLoading && selectedDocument ? (
          <div
            style={{
              alignItems: "center",
              backgroundColor: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: 14,
              display: "flex",
              flexWrap: "wrap",
              gap: 10,
              justifyContent: "space-between",
              padding: 12,
            }}
          >
            <div style={{ display: "grid", gap: 4 }}>
              <strong>{selectedDocument.title}</strong>
              <span style={{ color: "#64748b", fontSize: 13 }}>
                最近更新：{new Date(selectedDocument.updated_at).toLocaleString("zh-CN")}
              </span>
            </div>
            {renderStatus(selectedDocument.status)}
          </div>
        ) : null}
        {!isLoading && !selectedDocument ? <p style={{ color: "#64748b", margin: 0 }}>还没有资料。</p> : null}
      </section>
    );
  }

  if (variant === "compact") {
    return (
      <div style={{ display: "grid", gap: 18 }}>
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "grid", gap: 6 }}>
            <strong style={{ color: "#0f172a", fontSize: 18 }}>上传或补充资料</strong>
            <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>
              这里保留最常用的资料动作：拖拽上传、选择文件、查看资料状态，以及在需要时重建索引。
            </p>
          </div>
          <form onSubmit={handleUpload} style={{ display: "grid", gap: 12 }}>
            {uploadZone}
            {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
              <button disabled={isUploading} type="submit">
                {isUploading ? "正在上传..." : "上传资料"}
              </button>
              <button onClick={openFilePicker} type="button">
                选择文件
              </button>
              <span style={{ color: "#475569" }}>当前共 {documents.length} 份资料</span>
            </div>
          </form>
        </div>

        {isLoading ? <p>正在加载资料...</p> : null}
        {!isLoading && documents.length === 0 ? <p>还没有资料。先上传一份材料，再继续对话或动作。</p> : null}

        {documents.length > 0 ? (
          <div
            style={{
              display: "grid",
              gap: 16,
              gridTemplateColumns: "minmax(240px, 320px) minmax(0, 1fr)",
            }}
          >
            <div style={{ display: "grid", gap: 10, maxHeight: 360, overflowY: "auto" }}>
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
                      更新时间：{new Date(document.updated_at).toLocaleString("zh-CN")}
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
                <div>更新时间：{new Date(selectedDocument.updated_at).toLocaleString("zh-CN")}</div>
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
                    <div>资料 ID：{selectedDocument.id}</div>
                    <div>存储路径：{selectedDocument.file_path ?? "无"}</div>
                  </div>
                </details>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <>
      <SectionCard title="上传资料" description="当前上传流程会同步完成 ingest 和索引。">
        <form onSubmit={handleUpload} style={{ display: "grid", gap: 12, maxWidth: 560 }}>
          {uploadZone}
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
            <button disabled={isUploading} type="submit">
              {isUploading ? "正在上传..." : "上传资料"}
            </button>
            <button onClick={openFilePicker} type="button">
              选择文件
            </button>
          </div>
        </form>
      </SectionCard>

      <SectionCard title="资料列表" description={`工作区：${workspaceId}`}>
        {isLoading ? <p>正在加载资料...</p> : null}
        {!isLoading && documents.length === 0 ? <p>还没有上传任何资料。</p> : null}
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {documents.map((document) => (
            <li key={document.id} style={{ marginBottom: 12 }}>
              <div style={{ alignItems: "center", display: "flex", gap: 10, marginBottom: 6 }}>
                <strong>{document.title}</strong>
                {renderStatus(document.status)}
              </div>
              <div>来源类型：{getSourceTypeLabel(document.source_type)}</div>
              <div>MIME 类型：{document.mime_type ?? "未知"}</div>
              <div>存储路径：{document.file_path ?? "无"}</div>
              <div>更新时间：{new Date(document.updated_at).toLocaleString("zh-CN")}</div>
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
