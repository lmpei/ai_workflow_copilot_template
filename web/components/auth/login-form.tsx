"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { isApiClientError, loginUser } from "../../lib/api";
import { getAuthRoutes, storeLoginSession } from "../../lib/auth";
import type { PublicDemoSettingsRecord } from "../../lib/types";
import PublicDemoNotice from "../public-demo/public-demo-notice";
import SectionCard from "../ui/section-card";
import { useAuthSession } from "./use-auth-session";

type LoginFormProps = {
  publicDemoSettings?: PublicDemoSettingsRecord | null;
};

export default function LoginForm({ publicDemoSettings = null }: LoginFormProps) {
  const router = useRouter();
  const { session, isReady } = useAuthSession();
  const authRoutes = getAuthRoutes();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const registrationDisabled =
    publicDemoSettings?.public_demo_mode && !publicDemoSettings.registration_enabled;

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await loginUser({ email, password });
      storeLoginSession(response);
      router.push("/workspaces");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Login">Loading session...</SectionCard>;
  }

  if (session) {
    return (
      <SectionCard title="Already signed in" description={`Signed in as ${session.user.email}.`}>
        <p>
          Continue to <Link href="/workspaces">workspaces</Link>.
        </p>
      </SectionCard>
    );
  }

  return (
    <>
      {publicDemoSettings ? (
        <PublicDemoNotice
          settings={publicDemoSettings}
          title="Public Demo Access"
          description="Use this page to sign in to the public demo. Registration availability is controlled by the current demo guardrails."
        />
      ) : null}
      <SectionCard title="Sign in" description="Sign in to access public-demo workspaces, documents, and workflow surfaces.">
        <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12, maxWidth: 420 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Email</span>
            <input
              autoComplete="email"
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Password</span>
            <input
              autoComplete="current-password"
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button disabled={isSubmitting} type="submit">
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
        {registrationDisabled ? (
          <p>Self-serve registration is temporarily disabled for this public demo.</p>
        ) : (
          <p>
            Need an account? <Link href={authRoutes.register}>Register</Link>
          </p>
        )}
      </SectionCard>
    </>
  );
}
