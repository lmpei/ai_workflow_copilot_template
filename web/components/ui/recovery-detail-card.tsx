import type { RecoveryDetailRecord } from "../../lib/types";

type RecoveryDetailCardProps = {
  title?: string;
  detail: RecoveryDetailRecord;
  emptyText?: string;
};

function renderOptionalLine(label: string, value: string | undefined) {
  if (!value) {
    return null;
  }

  return (
    <div>
      <strong>{label}:</strong> {value}
    </div>
  );
}

export default function RecoveryDetailCard({
  title = "恢复详情",
  detail,
  emptyText = "目前还没有记录恢复元数据。",
}: RecoveryDetailCardProps) {
  const history = detail.history ?? [];
  const metadataEntries = Object.entries(detail.metadata ?? {});

  return (
    <div
      style={{
        backgroundColor: "#f8fafc",
        border: "1px solid #cbd5e1",
        borderRadius: 16,
        display: "grid",
        gap: 12,
        padding: 16,
      }}
    >
      <div style={{ display: "grid", gap: 6 }}>
        <div style={{ color: "#475569", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>{title}</div>
        <div>
          <strong>当前状态：</strong> {detail.state}
        </div>
        {renderOptionalLine("最近动作", detail.last_action)}
        {renderOptionalLine("原因", detail.reason)}
        {renderOptionalLine("请求人", detail.requested_by)}
        {renderOptionalLine("请求时间", detail.requested_at)}
        {renderOptionalLine("执行人", detail.applied_by)}
        {renderOptionalLine("执行时间", detail.applied_at)}
        {renderOptionalLine("来源任务", detail.source_task_id)}
        {renderOptionalLine("目标任务", detail.target_task_id)}
        {renderOptionalLine("来源评测运行", detail.source_eval_run_id)}
        {renderOptionalLine("目标评测运行", detail.target_eval_run_id)}
      </div>

      {metadataEntries.length > 0 ? (
        <div>
          <strong>运行时元数据</strong>
          <ul style={{ marginBottom: 0, marginTop: 8 }}>
            {metadataEntries.map(([key, value]) => (
              <li key={key}>
                {key}: {typeof value === "string" ? value : JSON.stringify(value)}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div>
        <strong>恢复历史</strong>
        {history.length === 0 ? (
          <p style={{ marginBottom: 0, marginTop: 8 }}>{emptyText}</p>
        ) : (
          <ul style={{ display: "grid", gap: 10, listStyle: "none", margin: "12px 0 0", padding: 0 }}>
            {history.map((entry, index) => {
              const entryMetadata = Object.entries(entry.metadata ?? {});
              return (
                <li
                  key={`${entry.event}-${entry.at}-${index}`}
                  style={{
                    backgroundColor: "#ffffff",
                    border: "1px solid #cbd5e1",
                    borderRadius: 12,
                    padding: 12,
                  }}
                >
                  <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <strong>{entry.event}</strong>
                    {entry.state ? (
                      <span style={{ color: "#475569", fontSize: 12, textTransform: "uppercase" }}>{entry.state}</span>
                    ) : null}
                  </div>
                  <div style={{ color: "#475569", marginTop: 6 }}>{new Date(entry.at).toLocaleString()}</div>
                  {entry.by ? <div style={{ marginTop: 6 }}><strong>操作人：</strong> {entry.by}</div> : null}
                  {entry.reason ? <div style={{ marginTop: 6 }}><strong>原因：</strong> {entry.reason}</div> : null}
                  {entryMetadata.length > 0 ? (
                    <div style={{ marginTop: 8 }}>
                      <strong>元数据</strong>
                      <ul style={{ marginBottom: 0, marginTop: 6 }}>
                        {entryMetadata.map(([key, value]) => (
                          <li key={key}>
                            {key}: {typeof value === "string" ? value : JSON.stringify(value)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
