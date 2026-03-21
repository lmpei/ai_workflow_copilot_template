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
  title = "Recovery detail",
  detail,
  emptyText = "No recovery metadata has been recorded yet.",
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
          <strong>Current state:</strong> {detail.state}
        </div>
        {renderOptionalLine("Last action", detail.last_action)}
        {renderOptionalLine("Reason", detail.reason)}
        {renderOptionalLine("Requested by", detail.requested_by)}
        {renderOptionalLine("Requested at", detail.requested_at)}
        {renderOptionalLine("Applied by", detail.applied_by)}
        {renderOptionalLine("Applied at", detail.applied_at)}
        {renderOptionalLine("Source task", detail.source_task_id)}
        {renderOptionalLine("Target task", detail.target_task_id)}
        {renderOptionalLine("Source eval run", detail.source_eval_run_id)}
        {renderOptionalLine("Target eval run", detail.target_eval_run_id)}
      </div>

      {metadataEntries.length > 0 ? (
        <div>
          <strong>Runtime metadata</strong>
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
        <strong>Recovery history</strong>
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
                  {entry.by ? <div style={{ marginTop: 6 }}><strong>Actor:</strong> {entry.by}</div> : null}
                  {entry.reason ? <div style={{ marginTop: 6 }}><strong>Reason:</strong> {entry.reason}</div> : null}
                  {entryMetadata.length > 0 ? (
                    <div style={{ marginTop: 8 }}>
                      <strong>Metadata</strong>
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
