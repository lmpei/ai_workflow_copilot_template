"use client";

import { useEffect, useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

type AuthRequiredProps = {
  title?: string;
  description?: string;
};

function resolveLoginHref(pathname: string | null, queryString: string) {
  const nextPath = pathname ? `${pathname}${queryString ? `?${queryString}` : ""}` : "/";
  const safeNextPath = nextPath.startsWith("/") && !nextPath.startsWith("//") ? nextPath : "/";
  return `/?auth=1&next=${encodeURIComponent(safeNextPath)}`;
}

export default function AuthRequired(_props: AuthRequiredProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const loginHref = useMemo(
    () => resolveLoginHref(pathname, searchParams.toString()),
    [pathname, searchParams],
  );

  useEffect(() => {
    router.replace(loginHref);
  }, [loginHref, router]);

  return null;
}
