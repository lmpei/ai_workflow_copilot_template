import type { AuthSession, LoginResponsePayload } from "./types";

export type AuthRoutes = {
  login: string;
  register: string;
};

const ACCESS_TOKEN_KEY = "ai-workflow-copilot.access-token";
const USER_KEY = "ai-workflow-copilot.user";

export const AUTH_CHANGE_EVENT = "ai-workflow-auth-change";

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function notifyAuthChange(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));
  }
}

export function getAuthRoutes(): AuthRoutes {
  return {
    login: "/?auth=1",
    register: "/?auth=1",
  };
}

export function createAuthSession(payload: LoginResponsePayload): AuthSession {
  return {
    accessToken: payload.access_token,
    user: payload.user,
  };
}

export function getStoredSession(): AuthSession | null {
  if (!canUseStorage()) {
    return null;
  }

  const accessToken = window.localStorage.getItem(ACCESS_TOKEN_KEY);
  const rawUser = window.localStorage.getItem(USER_KEY);

  if (!accessToken || !rawUser) {
    return null;
  }

  try {
    return {
      accessToken,
      user: JSON.parse(rawUser) as AuthSession["user"],
    };
  } catch {
    clearStoredSession();
    return null;
  }
}

export function storeSession(session: AuthSession): AuthSession {
  if (canUseStorage()) {
    window.localStorage.setItem(ACCESS_TOKEN_KEY, session.accessToken);
    window.localStorage.setItem(USER_KEY, JSON.stringify(session.user));
    notifyAuthChange();
  }
  return session;
}

export function storeLoginSession(payload: LoginResponsePayload): AuthSession {
  return storeSession(createAuthSession(payload));
}

export function clearStoredSession(): void {
  if (canUseStorage()) {
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    window.localStorage.removeItem(USER_KEY);
    notifyAuthChange();
  }
}

export function isAuthImplemented(): boolean {
  return true;
}
