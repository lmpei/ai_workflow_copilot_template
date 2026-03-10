"use client";

import { useEffect, useState } from "react";

import { AUTH_CHANGE_EVENT, getStoredSession } from "../../lib/auth";
import type { AuthSession } from "../../lib/types";

type UseAuthSessionResult = {
  session: AuthSession | null;
  isReady: boolean;
};

export function useAuthSession(): UseAuthSessionResult {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const syncSession = () => {
      setSession(getStoredSession());
      setIsReady(true);
    };

    syncSession();
    window.addEventListener(AUTH_CHANGE_EVENT, syncSession);
    window.addEventListener("storage", syncSession);

    return () => {
      window.removeEventListener(AUTH_CHANGE_EVENT, syncSession);
      window.removeEventListener("storage", syncSession);
    };
  }, []);

  return {
    session,
    isReady,
  };
}
