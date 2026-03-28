"use client";

import Link from "next/link";

import SectionCard from "../ui/section-card";

type AuthRequiredProps = {
  title?: string;
  description?: string;
};

export default function AuthRequired({
  title = "需要先登录",
  description = "这个页面需要已登录的账号会话。",
}: AuthRequiredProps) {
  return (
    <SectionCard title={title} description={description}>
      <p>
        请先 <Link href="/login">登录</Link>，如果还没有账号，可以先去 <Link href="/register">注册</Link>。
      </p>
    </SectionCard>
  );
}
