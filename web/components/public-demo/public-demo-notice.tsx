import SectionCard from "../ui/section-card";
import type { PublicDemoSettingsRecord } from "../../lib/types";

type PublicDemoNoticeProps = {
  settings: PublicDemoSettingsRecord;
  title?: string;
  description?: string;
  showRegistrationStatus?: boolean;
};

function formatUploadLimit(settings: PublicDemoSettingsRecord): string {
  const megabytes = settings.max_upload_bytes / (1024 * 1024);
  if (Number.isInteger(megabytes)) {
    return `${megabytes.toFixed(0)} MB`;
  }
  return `${megabytes.toFixed(1)} MB`;
}

export default function PublicDemoNotice({
  settings,
  title = "Public Demo Limits",
  description = "This public demo keeps each account bounded so outside users can explore the workflow platform without hidden operator steps.",
  showRegistrationStatus = true,
}: PublicDemoNoticeProps) {
  if (!settings.public_demo_mode) {
    return null;
  }

  return (
    <SectionCard title={title} description={description}>
      <ul style={{ margin: 0, paddingLeft: 20 }}>
        {showRegistrationStatus ? (
          <li>
            Self-serve registration: {settings.registration_enabled ? "enabled" : "temporarily disabled"}
          </li>
        ) : null}
        <li>Workspaces per account: {settings.max_workspaces_per_user}</li>
        <li>Documents per workspace: {settings.max_documents_per_workspace}</li>
        <li>Tasks per workspace: {settings.max_tasks_per_workspace}</li>
        <li>Max upload size: {formatUploadLimit(settings)}</li>
      </ul>
    </SectionCard>
  );
}
