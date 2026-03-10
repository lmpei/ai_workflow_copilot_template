const INTERNAL_API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL || "http://server:8000/api/v1";

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
