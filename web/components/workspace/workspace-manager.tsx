"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { createWorkspace, isApiClientError, listWorkspaces } from "../../lib/api";
import { clearStoredSession } from "../../lib/auth";
import { workspaceTypes, type Workspace, type WorkspaceType } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

export default function WorkspaceManager() {
  const router = useRouter();
  const { session, isReady } = useAuthSession();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [name, setName] = useState("");
  const [type, setType] = useState<WorkspaceType>("research");
  const [description, setDescription] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!session) {
      setWorkspaces([]);
      return;
    }

    const loadWorkspaces = async () => {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        setWorkspaces(await listWorkspaces(session.accessToken));
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to load workspaces");
      } finally {
        setIsLoading(false);
      }
    };

    void loadWorkspaces();
  }, [session]);

  const handleCreateWorkspace = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const workspace = await createWorkspace(session.accessToken, {
        name,
        type,
        description: description || undefined,
      });
      setWorkspaces((currentWorkspaces) => [workspace, ...currentWorkspaces]);
      setName("");
      setType("research");
      setDescription("");
      router.push(`/workspaces/${workspace.id}`);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to create workspace");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = () => {
    clearStoredSession();
    router.push("/login");
  };

  if (!isReady) {
    return <SectionCard title="Workspaces">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to create and manage workspaces." />;
  }

  return (
    <>
      <SectionCard title="Current session" description={`Signed in as ${session.user.email}.`}>
        <button onClick={handleLogout} type="button">
          Log out
        </button>
      </SectionCard>

      <SectionCard title="Create workspace" description="Each workspace owns documents, chat traces, and metrics.">
        <form onSubmit={handleCreateWorkspace} style={{ display: "grid", gap: 12, maxWidth: 520 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Name</span>
            <input onChange={(event) => setName(event.target.value)} required type="text" value={name} />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Type</span>
            <select onChange={(event) => setType(event.target.value as WorkspaceType)} value={type}>
              {workspaceTypes.map((workspaceType) => (
                <option key={workspaceType} value={workspaceType}>
                  {workspaceType}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Description</span>
            <textarea
              onChange={(event) => setDescription(event.target.value)}
              rows={3}
              value={description}
            />
          </label>
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button disabled={isSubmitting} type="submit">
            {isSubmitting ? "Creating..." : "Create workspace"}
          </button>
        </form>
      </SectionCard>

      <SectionCard title="Workspace list" description="Open a workspace to manage documents, chat, and metrics.">
        {isLoading ? <p>Loading workspaces...</p> : null}
        {!isLoading && workspaces.length === 0 ? <p>No workspaces yet.</p> : null}
        <ul>
          {workspaces.map((workspace) => (
            <li key={workspace.id} style={{ marginBottom: 10 }}>
              <div>
                <Link href={`/workspaces/${workspace.id}`}>{workspace.name}</Link> ({workspace.type})
              </div>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <Link href={`/workspaces/${workspace.id}/documents`}>Documents</Link>
                <Link href={`/workspaces/${workspace.id}/chat`}>Chat</Link>
                <Link href={`/workspaces/${workspace.id}/analytics`}>Analytics</Link>
              </div>
            </li>
          ))}
        </ul>
      </SectionCard>
    </>
  );
}
