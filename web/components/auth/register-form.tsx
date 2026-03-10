"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { isApiClientError, loginUser, registerUser } from "../../lib/api";
import { getAuthRoutes, storeLoginSession } from "../../lib/auth";
import SectionCard from "../ui/section-card";
import { useAuthSession } from "./use-auth-session";

export default function RegisterForm() {
  const router = useRouter();
  const { session, isReady } = useAuthSession();
  const authRoutes = getAuthRoutes();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      await registerUser({ name, email, password });
      const loginResponse = await loginUser({ email, password });
      storeLoginSession(loginResponse);
      router.push("/workspaces");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Registration failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Register">Loading session...</SectionCard>;
  }

  if (session) {
    return (
      <SectionCard title="Account already active" description={`Signed in as ${session.user.email}.`}>
        <p>
          Continue to <Link href="/workspaces">workspaces</Link>.
        </p>
      </SectionCard>
    );
  }

  return (
    <SectionCard title="Create account" description="Phase 1 uses bearer-token auth stored in the browser.">
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12, maxWidth: 420 }}>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Name</span>
          <input onChange={(event) => setName(event.target.value)} required type="text" value={name} />
        </label>
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
            autoComplete="new-password"
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
        </label>
        {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
        <button disabled={isSubmitting} type="submit">
          {isSubmitting ? "Creating account..." : "Create account"}
        </button>
      </form>
      <p>
        Already registered? <Link href={authRoutes.login}>Sign in</Link>
      </p>
    </SectionCard>
  );
}
