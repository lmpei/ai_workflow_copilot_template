import { redirect } from "next/navigation";

function resolveNextPath(rawNextPath: string | string[] | undefined) {
  const nextPath = Array.isArray(rawNextPath) ? rawNextPath[0] : rawNextPath;
  if (!nextPath) {
    return "/";
  }

  return nextPath.startsWith("/") && !nextPath.startsWith("//") ? nextPath : "/";
}

function buildAuthOverlayHref(nextPath: string) {
  return nextPath === "/"
    ? "/?auth=1"
    : `/?auth=1&next=${encodeURIComponent(nextPath)}`;
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const nextPath = resolveNextPath(resolvedSearchParams?.next);

  redirect(buildAuthOverlayHref(nextPath));
}
