import type { PublicDemoSettingsRecord } from "../../lib/types";
import SectionCard from "../ui/section-card";

type PublicDemoNoticeProps = {
  settings: PublicDemoSettingsRecord;
  title?: string;
  description?: string;
  showRegistrationStatus?: boolean;
  variant?: "card" | "compact";
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
  title = "公网 Demo 限制",
  description = "这个公网 demo 会对每个账号施加明确限制，让外部用户在没有隐含运维步骤的前提下体验工作流平台。",
  showRegistrationStatus = true,
  variant = "card",
}: PublicDemoNoticeProps) {
  if (!settings.public_demo_mode) {
    return null;
  }

  const content = (
    <ul style={{ margin: 0, paddingLeft: 20 }}>
      {showRegistrationStatus ? <li>自助注册：{settings.registration_enabled ? "已开放" : "暂时关闭"}</li> : null}
      <li>每个账号最多工作区数：{settings.max_workspaces_per_user}</li>
      <li>每个工作区最多文档数：{settings.max_documents_per_workspace}</li>
      <li>每个工作区最多任务数：{settings.max_tasks_per_workspace}</li>
      <li>单次最大上传大小：{formatUploadLimit(settings)}</li>
    </ul>
  );

  if (variant === "compact") {
    return (
      <>
        {description ? <p style={{ color: "#52525b", marginTop: 0 }}>{description}</p> : null}
        {content}
      </>
    );
  }

  return (
    <SectionCard title={title} description={description}>
      {content}
    </SectionCard>
  );
}
