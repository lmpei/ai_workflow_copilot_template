"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { isApiClientError, loginUser, registerUser } from "../../lib/api";
import { getAuthRoutes, storeLoginSession } from "../../lib/auth";
import type { PublicDemoSettingsRecord } from "../../lib/types";
import PublicDemoNotice from "../public-demo/public-demo-notice";
import SectionCard from "../ui/section-card";
import { useAuthSession } from "./use-auth-session";

type RegisterFormProps = {
  publicDemoSettings?: PublicDemoSettingsRecord | null;
};

export default function RegisterForm({ publicDemoSettings = null }: RegisterFormProps) {
  const router = useRouter();
  const { session, isReady } = useAuthSession();
  const authRoutes = getAuthRoutes();
  const [name, setName] = useState("");
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
      await registerUser({ name, email, password });
      const loginResponse = await loginUser({ email, password });
      storeLoginSession(loginResponse);
      router.push("/");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "注册失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="注册">正在加载会话...</SectionCard>;
  }

  if (session) {
    return (
      <SectionCard title="账号已登录" description={`当前账号：${session.user.email}`}>
        <p>
          前往 <Link href="/">项目入口</Link> 或 <Link href="/workspaces">工作区中心</Link> 继续。
        </p>
      </SectionCard>
    );
  }

  if (registrationDisabled) {
    return (
      <>
        {publicDemoSettings ? (
          <PublicDemoNotice
            settings={publicDemoSettings}
            title="公网 Demo 访问"
            description="当前已关闭自助注册，因此这个公开 demo 目前需要使用已有账号登录。"
          />
        ) : null}
        <SectionCard title="暂不开放注册" description="当前这一轮公开 demo 暂时关闭了自助注册。">
          <p>
            请使用已有账号前往 <Link href={authRoutes.login}>登录</Link>，或稍后再试。
          </p>
        </SectionCard>
      </>
    );
  }

  return (
    <>
      {publicDemoSettings ? (
        <PublicDemoNotice
          settings={publicDemoSettings}
          title="公网 Demo 限制"
          description="你可以在当前限制范围内创建账号并体验这个项目。"
        />
      ) : null}
      <SectionCard title="创建账号" description="创建一个受限的公开 demo 账号，然后进入当前项目。">
        <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12, maxWidth: 420 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>姓名</span>
            <input onChange={(event) => setName(event.target.value)} required type="text" value={name} />
          </label>
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
              autoComplete="new-password"
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button disabled={isSubmitting} type="submit">
            {isSubmitting ? "正在创建账号..." : "创建账号"}
          </button>
        </form>
        <p>
          已经注册过？前往 <Link href={authRoutes.login}>登录</Link>
        </p>
      </SectionCard>
    </>
  );
}
