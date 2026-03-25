"use client";

import Link from "next/link";

import SectionCard from "../ui/section-card";

type AuthRequiredProps = {
  title?: string;
  description?: string;
};

export default function AuthRequired({
  title = "Login required",
  description = "This page requires an authenticated account session.",
}: AuthRequiredProps) {
  return (
    <SectionCard title={title} description={description}>
      <p>
        <Link href="/login">Log in</Link> or <Link href="/register">create an account</Link> to
        continue.
      </p>
    </SectionCard>
  );
}
