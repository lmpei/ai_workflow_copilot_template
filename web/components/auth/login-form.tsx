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
      router.push("/");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "登录失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="登录">正在加载会话...</SectionCard>;
  }

  if (session) {
    return (
      <SectionCard title="已登录" description={`当前账号：${session.user.email}`}>
        <p>
          前往 <Link href="/">项目入口</Link> 或 <Link href="/workspaces">工作区中心</Link> 继续。
        </p>
      </SectionCard>
    );
  }

  return (
    <>
      {publicDemoSettings ? (
        <PublicDemoNotice
          settings={publicDemoSettings}
          title="公网 Demo 访问"
          description="使用这个页面登录当前项目的公开 demo。是否允许注册由当前 demo 策略控制。"
        />
      ) : null}
      <SectionCard title="登录" description="登录后进入这个项目，再继续打开工作区和工作台。">
        <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12, maxWidth: 420 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>邮箱</span>
            <input
              autoComplete="email"
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>密码</span>
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
            {isSubmitting ? "正在登录..." : "登录"}
          </button>
        </form>
        {registrationDisabled ? (
          <p>当前公网 demo 暂时关闭自助注册。</p>
        ) : (
          <p>
            还没有账号？前往 <Link href={authRoutes.register}>注册</Link>
          </p>
        )}
      </SectionCard>
    </>
  );
}
