import { clearStoredSession } from "./auth";
import type {
  ChatRequestPayload,
  ChatResponsePayload,
  DocumentRecord,
  LoginRequestPayload,
  LoginResponsePayload,
  RegisterRequestPayload,
  User,
  Workspace,
  WorkspaceCreatePayload,
  WorkspaceMetrics,
} from "./types";

const INTERNAL_API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL || "http://server:8000/api/v1";
const PUBLIC_API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

type ApiErrorResponse = {
  status: "error";
  code: number;
};

type ApiUnreachableResponse = {
  status: "unreachable";
};

export type HealthResponse =
  | {
      status: string;
    }
  | ApiErrorResponse
  | ApiUnreachableResponse;

type ApiErrorPayload = {
  detail?: string;
};

export class ApiClientError extends Error {
  status: number;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiClientError";
    this.status = status;
  }
}

export function isApiClientError(error: unknown): error is ApiClientError {
  return error instanceof ApiClientError;
}

export async function fetchApiJson<T>(
  path: string,
): Promise<T | ApiErrorResponse | ApiUnreachableResponse> {
  try {
    const response = await fetch(`${INTERNAL_API_BASE_URL}${path}`, { cache: "no-store" });
    if (!response.ok) {
      return { status: "error", code: response.status };
    }
    return (await response.json()) as T;
  } catch {
    return { status: "unreachable" };
  }
}

export async function getHealth(): Promise<HealthResponse> {
  return fetchApiJson<{ status: string }>("/health");
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    if (typeof payload.detail === "string" && payload.detail.length > 0) {
      return payload.detail;
    }
  } catch {
    return response.statusText || `Request failed with status ${response.status}`;
  }

  return response.statusText || `Request failed with status ${response.status}`;
}

async function fetchBrowserApiJson<T>(
  path: string,
  init: RequestInit = {},
  accessToken?: string,
): Promise<T> {
  const headers = new Headers(init.headers);

  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;

  try {
    response = await fetch(`${PUBLIC_API_BASE_URL}${path}`, {
      ...init,
      headers,
      cache: "no-store",
    });
  } catch {
    throw new ApiClientError(0, "API unreachable");
  }

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredSession();
    }

    throw new ApiClientError(response.status, await parseErrorDetail(response));
  }

  return (await response.json()) as T;
}

export async function registerUser(payload: RegisterRequestPayload): Promise<User> {
  return fetchBrowserApiJson<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function loginUser(payload: LoginRequestPayload): Promise<LoginResponsePayload> {
  return fetchBrowserApiJson<LoginResponsePayload>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getCurrentUser(accessToken: string): Promise<User> {
  return fetchBrowserApiJson<User>("/auth/me", {}, accessToken);
}

export async function listWorkspaces(accessToken: string): Promise<Workspace[]> {
  return fetchBrowserApiJson<Workspace[]>("/workspaces", {}, accessToken);
}

export async function createWorkspace(
  accessToken: string,
  payload: WorkspaceCreatePayload,
): Promise<Workspace> {
  return fetchBrowserApiJson<Workspace>(
    "/workspaces",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    accessToken,
  );
}

export async function getWorkspace(accessToken: string, workspaceId: string): Promise<Workspace> {
  return fetchBrowserApiJson<Workspace>(`/workspaces/${workspaceId}`, {}, accessToken);
}

export async function listWorkspaceDocuments(
  accessToken: string,
  workspaceId: string,
): Promise<DocumentRecord[]> {
  return fetchBrowserApiJson<DocumentRecord[]>(
    `/workspaces/${workspaceId}/documents`,
    {},
    accessToken,
  );
}

export async function uploadWorkspaceDocument(
  accessToken: string,
  workspaceId: string,
  file: File,
): Promise<DocumentRecord> {
  const formData = new FormData();
  formData.append("file", file);

  return fetchBrowserApiJson<DocumentRecord>(
    `/workspaces/${workspaceId}/documents/upload`,
    {
      method: "POST",
      body: formData,
    },
    accessToken,
  );
}

export async function sendWorkspaceChat(
  accessToken: string,
  workspaceId: string,
  payload: ChatRequestPayload,
): Promise<ChatResponsePayload> {
  return fetchBrowserApiJson<ChatResponsePayload>(
    `/workspaces/${workspaceId}/chat`,
    {
      method: "POST",
      body: JSON.stringify({
        mode: "rag",
        ...payload,
      }),
    },
    accessToken,
  );
}

export async function getWorkspaceMetrics(
  accessToken: string,
  workspaceId: string,
): Promise<WorkspaceMetrics> {
  return fetchBrowserApiJson<WorkspaceMetrics>(
    `/workspaces/${workspaceId}/metrics`,
    {},
    accessToken,
  );
}
