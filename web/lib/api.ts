import { clearStoredSession } from "./auth";
import type {
  ChatRequestPayload,
  ChatResponsePayload,
  DocumentRecord,
  EvalDatasetCreatePayload,
  EvalDatasetRecord,
  EvalResultRecord,
  EvalRunCreatePayload,
  EvalRunRecord,
  JobHiringPacketRecord,
  JobHiringPacketSummaryRecord,
  LoginRequestPayload,
  LoginResponsePayload,
  PublicDemoSettingsRecord,
  PublicDemoTemplateRecord,
  PublicDemoWorkspaceSeedRecord,
  RegisterRequestPayload,
  ResearchAnalysisReviewResponse,
  ResearchAnalysisRunCreatePayload,
  ResearchAnalysisRunRecord,
  ResearchAssetComparisonRecord,
  ResearchAssetRecord,
  ResearchAssetSummaryRecord,
  ScenarioModuleRecord,
  SupportCaseRecord,
  SupportCaseSummaryRecord,
  TaskCreatePayload,
  TaskRecord,
  TraceRecord,
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
export async function getScenarioModules(): Promise<ScenarioModuleRecord[] | ApiErrorResponse | ApiUnreachableResponse> {
  return fetchApiJson<ScenarioModuleRecord[]>("/scenario-modules");
}
export async function getPublicDemoSettings(): Promise<
  PublicDemoSettingsRecord | ApiErrorResponse | ApiUnreachableResponse
> {
  return fetchApiJson<PublicDemoSettingsRecord>("/public-demo");
}
export async function getPublicDemoTemplates(): Promise<
  PublicDemoTemplateRecord[] | ApiErrorResponse | ApiUnreachableResponse
> {
  return fetchApiJson<PublicDemoTemplateRecord[]>("/public-demo/templates");
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

export async function readPublicDemoSettings(): Promise<PublicDemoSettingsRecord> {
  return fetchBrowserApiJson<PublicDemoSettingsRecord>("/public-demo");
}

export async function listPublicDemoTemplates(): Promise<PublicDemoTemplateRecord[]> {
  return fetchBrowserApiJson<PublicDemoTemplateRecord[]>("/public-demo/templates");
}

export async function createPublicDemoWorkspaceFromTemplate(
  accessToken: string,
  templateId: string,
): Promise<PublicDemoWorkspaceSeedRecord> {
  return fetchBrowserApiJson<PublicDemoWorkspaceSeedRecord>(
    `/public-demo/templates/${templateId}/workspaces`,
    {
      method: "POST",
    },
    accessToken,
  );
}

export async function listScenarioModules(): Promise<ScenarioModuleRecord[]> {
  return fetchBrowserApiJson<ScenarioModuleRecord[]>("/scenario-modules");
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

export async function reindexDocument(
  accessToken: string,
  documentId: string,
): Promise<DocumentRecord> {
  return fetchBrowserApiJson<DocumentRecord>(
    `/documents/${documentId}/reindex`,
    {
      method: "POST",
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

export async function createWorkspaceResearchAnalysisRun(
  accessToken: string,
  workspaceId: string,
  payload: ResearchAnalysisRunCreatePayload,
): Promise<ResearchAnalysisRunRecord> {
  return fetchBrowserApiJson<ResearchAnalysisRunRecord>(
    `/workspaces/${workspaceId}/research-analysis-runs`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    accessToken,
  );
}

export async function listWorkspaceResearchAnalysisRuns(
  accessToken: string,
  workspaceId: string,
  limit = 8,
): Promise<ResearchAnalysisRunRecord[]> {
  return fetchBrowserApiJson<ResearchAnalysisRunRecord[]>(
    `/workspaces/${workspaceId}/research-analysis-runs?limit=${limit}`,
    {},
    accessToken,
  );
}

export async function getResearchAnalysisRun(
  accessToken: string,
  runId: string,
): Promise<ResearchAnalysisRunRecord> {
  return fetchBrowserApiJson<ResearchAnalysisRunRecord>(`/research-analysis-runs/${runId}`, {}, accessToken);
}
export async function listWorkspaceResearchAnalysisRunReviews(
  accessToken: string,
  workspaceId: string,
  limit = 8,
): Promise<ResearchAnalysisReviewResponse> {
  return fetchBrowserApiJson<ResearchAnalysisReviewResponse>(
    `/workspaces/${workspaceId}/research-analysis-runs/review?limit=${limit}`,
    {},
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

export async function getWorkspaceAnalytics(
  accessToken: string,
  workspaceId: string,
): Promise<WorkspaceMetrics> {
  return fetchBrowserApiJson<WorkspaceMetrics>(
    `/workspaces/${workspaceId}/analytics`,
    {},
    accessToken,
  );
}

export async function listWorkspaceTraces(
  accessToken: string,
  workspaceId: string,
  limit = 20,
): Promise<TraceRecord[]> {
  return fetchBrowserApiJson<TraceRecord[]>(
    `/workspaces/${workspaceId}/traces?limit=${limit}`,
    {},
    accessToken,
  );
}

export async function createEvalDataset(
  accessToken: string,
  workspaceId: string,
  payload: EvalDatasetCreatePayload,
): Promise<EvalDatasetRecord> {
  return fetchBrowserApiJson<EvalDatasetRecord>(
    `/workspaces/${workspaceId}/evals/datasets`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    accessToken,
  );
}

export async function listEvalDatasets(
  accessToken: string,
  workspaceId: string,
): Promise<EvalDatasetRecord[]> {
  return fetchBrowserApiJson<EvalDatasetRecord[]>(
    `/workspaces/${workspaceId}/evals/datasets`,
    {},
    accessToken,
  );
}

export async function createEvalRun(
  accessToken: string,
  workspaceId: string,
  payload: EvalRunCreatePayload,
): Promise<EvalRunRecord> {
  return fetchBrowserApiJson<EvalRunRecord>(
    `/workspaces/${workspaceId}/evals/runs`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    accessToken,
  );
}

export async function getEvalRun(accessToken: string, evalRunId: string): Promise<EvalRunRecord> {
  return fetchBrowserApiJson<EvalRunRecord>(`/evals/runs/${evalRunId}`, {}, accessToken);
}

export async function cancelEvalRun(
  accessToken: string,
  evalRunId: string,
  payload?: { reason?: string },
): Promise<EvalRunRecord> {
  return fetchBrowserApiJson<EvalRunRecord>(
    `/evals/runs/${evalRunId}/cancel`,
    {
      method: "POST",
      body: JSON.stringify(payload ?? {}),
    },
    accessToken,
  );
}

export async function retryEvalRun(
  accessToken: string,
  evalRunId: string,
  payload?: { reason?: string },
): Promise<EvalRunRecord> {
  return fetchBrowserApiJson<EvalRunRecord>(
    `/evals/runs/${evalRunId}/retry`,
    {
      method: "POST",
      body: JSON.stringify(payload ?? {}),
    },
    accessToken,
  );
}

export async function listEvalRunResults(
  accessToken: string,
  evalRunId: string,
): Promise<EvalResultRecord[]> {
  return fetchBrowserApiJson<EvalResultRecord[]>(
    `/evals/runs/${evalRunId}/results`,
    {},
    accessToken,
  );
}

export async function createWorkspaceTask(
  accessToken: string,
  workspaceId: string,
  payload: TaskCreatePayload,
): Promise<TaskRecord> {
  return fetchBrowserApiJson<TaskRecord>(
    `/workspaces/${workspaceId}/tasks`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    accessToken,
  );
}

export async function listWorkspaceTasks(
  accessToken: string,
  workspaceId: string,
): Promise<TaskRecord[]> {
  return fetchBrowserApiJson<TaskRecord[]>(`/workspaces/${workspaceId}/tasks`, {}, accessToken);
}

export async function getTask(accessToken: string, taskId: string): Promise<TaskRecord> {
  return fetchBrowserApiJson<TaskRecord>(`/tasks/${taskId}`, {}, accessToken);
}

export async function listWorkspaceSupportCases(
  accessToken: string,
  workspaceId: string,
): Promise<SupportCaseSummaryRecord[]> {
  return fetchBrowserApiJson<SupportCaseSummaryRecord[]>(
    `/workspaces/${workspaceId}/support-cases`,
    {},
    accessToken,
  );
}

export async function getSupportCase(
  accessToken: string,
  caseId: string,
): Promise<SupportCaseRecord> {
  return fetchBrowserApiJson<SupportCaseRecord>(`/support-cases/${caseId}`, {}, accessToken);
}

export async function listWorkspaceJobHiringPackets(
  accessToken: string,
  workspaceId: string,
): Promise<JobHiringPacketSummaryRecord[]> {
  return fetchBrowserApiJson<JobHiringPacketSummaryRecord[]>(
    `/workspaces/${workspaceId}/job-hiring-packets`,
    {},
    accessToken,
  );
}

export async function getJobHiringPacket(
  accessToken: string,
  packetId: string,
): Promise<JobHiringPacketRecord> {
  return fetchBrowserApiJson<JobHiringPacketRecord>(`/job-hiring-packets/${packetId}`, {}, accessToken);
}
export async function cancelTask(
  accessToken: string,
  taskId: string,
  payload?: { reason?: string },
): Promise<TaskRecord> {
  return fetchBrowserApiJson<TaskRecord>(
    `/tasks/${taskId}/cancel`,
    {
      method: "POST",
      body: JSON.stringify(payload ?? {}),
    },
    accessToken,
  );
}

export async function retryTask(
  accessToken: string,
  taskId: string,
  payload?: { reason?: string },
): Promise<TaskRecord> {
  return fetchBrowserApiJson<TaskRecord>(
    `/tasks/${taskId}/retry`,
    {
      method: "POST",
      body: JSON.stringify(payload ?? {}),
    },
    accessToken,
  );
}

export async function createWorkspaceResearchAsset(
  accessToken: string,
  workspaceId: string,
  payload: { task_id: string; title?: string },
): Promise<ResearchAssetRecord> {
  return fetchBrowserApiJson<ResearchAssetRecord>(
    `/workspaces/${workspaceId}/research-assets`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    accessToken,
  );
}

export async function listWorkspaceResearchAssets(
  accessToken: string,
  workspaceId: string,
): Promise<ResearchAssetSummaryRecord[]> {
  return fetchBrowserApiJson<ResearchAssetSummaryRecord[]>(
    `/workspaces/${workspaceId}/research-assets`,
    {},
    accessToken,
  );
}

export async function getResearchAsset(
  accessToken: string,
  assetId: string,
): Promise<ResearchAssetRecord> {
  return fetchBrowserApiJson<ResearchAssetRecord>(`/research-assets/${assetId}`, {}, accessToken);
}
export async function compareResearchAssets(
  accessToken: string,
  payload: {
    left_asset_id: string;
    right_asset_id: string;
    left_revision_id?: string;
    right_revision_id?: string;
  },
): Promise<ResearchAssetComparisonRecord> {
  return fetchBrowserApiJson<ResearchAssetComparisonRecord>(
    "/research-assets/compare",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    accessToken,
  );
}
