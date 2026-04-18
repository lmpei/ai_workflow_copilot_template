"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { useRouter } from "next/navigation";

import { enterAuth, isApiClientError } from "../../lib/api";
import { storeLoginSession } from "../../lib/auth";

type AuthEntryOverlayProps = {
  nextPath: string;
};

const inputStyle = {
  background: "rgba(241, 245, 249, 0.82)",
  border: "1px solid rgba(191, 219, 254, 0.9)",
  borderRadius: 22,
  boxSizing: "border-box",
  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.58)",
  color: "#0f172a",
  display: "block",
  fontFamily: '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
  fontSize: 19,
  maxWidth: "100%",
  outline: "none",
  padding: "18px 22px",
  width: "100%",
} as const;

const labelStyle = {
  color: "#475569",
  fontFamily: '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
  fontSize: 13,
  fontWeight: 700,
  letterSpacing: "0.08em",
} as const;

export default function AuthEntryOverlay({ nextPath }: AuthEntryOverlayProps) {
  const router = useRouter();
  const [account, setAccount] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await enterAuth({ account, password });
      storeLoginSession(response);
      router.replace(nextPath);
    } catch (error) {
      setErrorMessage(
        isApiClientError(error) ? error.message : "进入失败，请稍后再试。",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        alignItems: "center",
        background:
          "linear-gradient(180deg, rgba(226,232,240,0.24) 0%, rgba(226,232,240,0.42) 100%)",
        backdropFilter: "blur(18px)",
        display: "grid",
        inset: 0,
        padding: "32px",
        position: "absolute",
        zIndex: 20,
      }}
    >
      <div
        aria-modal="true"
        role="dialog"
        style={{
          background:
            "linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,250,252,0.92) 100%)",
          border: "1px solid rgba(219, 234, 254, 0.95)",
          borderRadius: 36,
          boxShadow:
            "0 44px 120px rgba(15, 23, 42, 0.12), 0 0 0 1px rgba(255,255,255,0.46) inset",
          display: "grid",
          gap: 26,
          margin: "0 auto",
          maxWidth: 480,
          padding: "34px 34px 30px",
          width: "min(100%, 480px)",
        }}
      >
        <div style={{ display: "grid", gap: 10, justifyItems: "center" }}>
          <span
            style={{
              color: "#64748b",
              fontFamily: '"Consolas", "SFMono-Regular", monospace',
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: "0.18em",
              textTransform: "uppercase",
            }}
          >
            LMPAI WEAVE
          </span>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "grid", gap: 18, width: "100%" }}>
          <label style={{ display: "grid", gap: 8 }}>
            <span style={labelStyle}>账号</span>
            <input
              autoComplete="username"
              name="account"
              onChange={(event) => setAccount(event.target.value)}
              required
              style={inputStyle}
              type="text"
              value={account}
            />
          </label>

          <label style={{ display: "grid", gap: 8 }}>
            <span style={labelStyle}>密码</span>
            <input
              autoComplete="current-password"
              name="password"
              onChange={(event) => setPassword(event.target.value)}
              required
              style={inputStyle}
              type="password"
              value={password}
            />
          </label>

          {errorMessage ? (
            <p
              style={{
                color: "#b91c1c",
                fontFamily:
                  '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
                fontSize: 14,
                margin: "2px 4px 0",
                textAlign: "center",
              }}
            >
              {errorMessage}
            </p>
          ) : null}

          <button
            disabled={isSubmitting}
            style={{
              background: "#0f172a",
              border: "none",
              borderRadius: 999,
              boxSizing: "border-box",
              boxShadow: "0 22px 56px rgba(15, 23, 42, 0.18)",
              color: "#f8fafc",
              cursor: "pointer",
              display: "block",
              fontFamily:
                '"Aptos", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif',
              fontSize: 18,
              fontWeight: 700,
              maxWidth: "100%",
              marginTop: 6,
              padding: "18px 22px",
              width: "100%",
            }}
            type="submit"
          >
            {isSubmitting ? "进入中..." : "立即体验"}
          </button>
        </form>
      </div>
    </div>
  );
}
