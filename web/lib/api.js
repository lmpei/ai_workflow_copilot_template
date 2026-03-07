const INTERNAL_API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL || "http://server:8000/api/v1";

export async function fetchApiJson(path) {
  try {
    const response = await fetch(`${INTERNAL_API_BASE_URL}${path}`, { cache: "no-store" });
    if (!response.ok) {
      return { status: "error", code: response.status };
    }
    return await response.json();
  } catch {
    return { status: "unreachable" };
  }
}

export async function getHealth() {
  return fetchApiJson("/health");
}
