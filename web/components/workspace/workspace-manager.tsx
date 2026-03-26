"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  createPublicDemoWorkspaceFromTemplate,
  createWorkspace,
  isApiClientError,
  listPublicDemoTemplates,
  listWorkspaces,
  readPublicDemoSettings,
} from "../../lib/api";
import { clearStoredSession } from "../../lib/auth";
import {
  moduleTypes,
  type ModuleType,
  type PublicDemoSettingsRecord,
  type PublicDemoTemplateRecord,
  type Workspace,
} from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import PublicDemoNotice from "../public-demo/public-demo-notice";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

function getDemoTemplateId(workspace: Workspace): string | null {
  const value = workspace.module_config_json.demo_template_id;
  return typeof value === "string" && value.length > 0 ? value : null;
}

export default function WorkspaceManager() {
  const router = useRouter();
  const { session, isReady } = useAuthSession();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [publicDemoSettings, setPublicDemoSettings] = useState<PublicDemoSettingsRecord | null>(null);
  const [demoTemplates, setDemoTemplates] = useState<PublicDemoTemplateRecord[]>([]);
  const [name, setName] = useState("");
  const [moduleType, setModuleType] = useState<ModuleType>("research");
  const [description, setDescription] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [launchingTemplateId, setLaunchingTemplateId] = useState<string | null>(null);

  useEffect(() => {
    const loadPublicDemoContext = async () => {
      try {
        const [settings, templates] = await Promise.all([
          readPublicDemoSettings(),
          listPublicDemoTemplates(),
        ]);
        setPublicDemoSettings(settings);
        setDemoTemplates(templates);
      } catch {
        setPublicDemoSettings(null);
        setDemoTemplates([]);
      }
    };

    void loadPublicDemoContext();
  }, []);

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

  const workspaceLimitReached =
    publicDemoSettings?.public_demo_mode === true &&
    workspaces.length >= publicDemoSettings.max_workspaces_per_user;

  const demoTemplateMap = useMemo(
    () => Object.fromEntries(demoTemplates.map((template) => [template.template_id, template])) as Record<string, PublicDemoTemplateRecord>,
    [demoTemplates],
  );

  const handleCreateWorkspace = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session || workspaceLimitReached) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const workspace = await createWorkspace(session.accessToken, {
        name,
        module_type: moduleType,
        description: description || undefined,
      });
      setWorkspaces((currentWorkspaces) => [workspace, ...currentWorkspaces]);
      setName("");
      setModuleType("research");
      setDescription("");
      router.push(`/workspaces/${workspace.id}`);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to create workspace");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateGuidedDemo = async (templateId: string) => {
    if (!session || workspaceLimitReached) {
      return;
    }

    setLaunchingTemplateId(templateId);
    setErrorMessage(null);

    try {
      const seededWorkspace = await createPublicDemoWorkspaceFromTemplate(session.accessToken, templateId);
      setWorkspaces((currentWorkspaces) => [seededWorkspace.workspace, ...currentWorkspaces]);
      router.push(`/workspaces/${seededWorkspace.workspace.id}`);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to create the guided demo workspace");
    } finally {
      setLaunchingTemplateId(null);
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

      {publicDemoSettings ? (
        <PublicDemoNotice
          settings={publicDemoSettings}
          description="Public demo accounts are intentionally bounded so outside users can explore the system without hidden operator setup."
        />
      ) : null}

      <SectionCard
        title="Guided demo workspaces"
        description="Choose a seeded showcase path when you want to understand the platform quickly instead of starting from an empty workspace."
      >
        {publicDemoSettings?.public_demo_mode ? (
          <p style={{ marginTop: 0 }}>
            Current account usage: {workspaces.length} / {publicDemoSettings.max_workspaces_per_user} workspaces.
          </p>
        ) : null}
        {workspaceLimitReached ? (
          <p style={{ color: "#b45309", marginTop: 0 }}>
            This public-demo account has reached its workspace limit. Open an existing workspace or ask the operator to reset the account.
          </p>
        ) : null}
        {demoTemplates.length === 0 ? <p>No guided demo templates are available right now.</p> : null}
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          }}
        >
          {demoTemplates.map((template) => (
            <div
              key={template.template_id}
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 12,
                padding: 16,
              }}
            >
              <div style={{ alignItems: "center", display: "flex", gap: 8, marginBottom: 8 }}>
                <strong>{template.title}</strong>
                <span
                  style={{
                    backgroundColor: "#0f172a12",
                    borderRadius: 999,
                    color: "#0f172a",
                    fontSize: 12,
                    fontWeight: 600,
                    padding: "2px 10px",
                    textTransform: "uppercase",
                  }}
                >
                  {template.module_type}
                </span>
              </div>
              <p style={{ marginTop: 0 }}>{template.summary}</p>
              <p style={{ marginBottom: 8, marginTop: 0 }}>
                <strong>Seeded documents:</strong> {template.seeded_documents.map((document) => document.title).join(", ")}
              </p>
              <p style={{ marginBottom: 12, marginTop: 0 }}>
                <strong>Showcase path:</strong> {template.showcase_steps.map((step) => step.title).join(" -> ")}
              </p>
              <button
                disabled={workspaceLimitReached || launchingTemplateId !== null}
                onClick={() => void handleCreateGuidedDemo(template.template_id)}
                type="button"
              >
                {launchingTemplateId === template.template_id ? "Creating guided demo..." : "Create guided demo"}
              </button>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="Create workspace"
        description="Each workspace owns documents, chat traces, tasks, evals, and module-specific workflow state."
      >
        <form onSubmit={handleCreateWorkspace} style={{ display: "grid", gap: 12, maxWidth: 520 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Name</span>
            <input onChange={(event) => setName(event.target.value)} required type="text" value={name} />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Module</span>
            <select onChange={(event) => setModuleType(event.target.value as ModuleType)} value={moduleType}>
              {moduleTypes.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Description</span>
            <textarea onChange={(event) => setDescription(event.target.value)} rows={3} value={description} />
          </label>
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button disabled={isSubmitting || workspaceLimitReached} type="submit">
            {isSubmitting ? "Creating..." : "Create workspace"}
          </button>
        </form>
      </SectionCard>

      <SectionCard
        title="Workspace list"
        description="Open a workspace to manage documents, grounded chat, scenario tasks, and demo-ready module surfaces."
      >
        {isLoading ? <p>Loading workspaces...</p> : null}
        {!isLoading && workspaces.length === 0 ? <p>No workspaces yet.</p> : null}
        <ul>
          {workspaces.map((workspace) => {
            const demoTemplate = demoTemplateMap[getDemoTemplateId(workspace) ?? ""];

            return (
              <li key={workspace.id} style={{ marginBottom: 10 }}>
                <div>
                  <Link href={`/workspaces/${workspace.id}`}>{workspace.name}</Link>
                </div>
                <div>Active module: {workspace.module_type}</div>
                {demoTemplate ? <div>Guided demo: {demoTemplate.title}</div> : null}
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                  <Link href={`/workspaces/${workspace.id}/modules`}>Modules</Link>
                  <Link href={`/workspaces/${workspace.id}/documents`}>Documents</Link>
                  <Link href={`/workspaces/${workspace.id}/chat`}>Chat</Link>
                  <Link href={`/workspaces/${workspace.id}/tasks`}>Tasks</Link>
                  <Link href={`/workspaces/${workspace.id}/analytics`}>Analytics</Link>
                </div>
              </li>
            );
          })}
        </ul>
      </SectionCard>
    </>
  );
}