import type {
  ResearchAssetRecord,
  ResearchAssetRevisionRecord,
  ResearchAssetSummaryRecord,
} from "../../lib/types";
import SectionCard from "../ui/section-card";

type ResearchWorkbenchSectionProps = {
  researchAssets: ResearchAssetSummaryRecord[];
  selectedAssetId: string | null;
  selectedAsset: ResearchAssetRecord | null;
  isLoadingAssets: boolean;
  isLoadingSelectedAsset: boolean;
  onSelectAsset: (assetId: string) => void;
  onContinueAsset: (asset: ResearchAssetSummaryRecord | ResearchAssetRecord) => void;
  onContinueRevision: (asset: ResearchAssetRecord, revision: ResearchAssetRevisionRecord) => void;
  onOpenTask: (taskId: string | null) => void;
};

export default function ResearchWorkbenchSection({
  researchAssets,
  selectedAssetId,
  selectedAsset,
  isLoadingAssets,
  isLoadingSelectedAsset,
  onSelectAsset,
  onContinueAsset,
  onContinueRevision,
  onOpenTask,
}: ResearchWorkbenchSectionProps) {
  return (
    <SectionCard
      title="Research workbench"
      description="Persistent research assets let you reopen a saved report, review revision history, and continue the same investigation without losing lineage."
    >
      {isLoadingAssets ? <p>Loading research workbench...</p> : null}
      {!isLoadingAssets && researchAssets.length === 0 ? (
        <p>No saved research assets yet. Save a completed research run to start the workbench lifecycle.</p>
      ) : null}
      {researchAssets.length > 0 ? (
        <div
          style={{
            display: "grid",
            gap: 16,
            gridTemplateColumns: "minmax(280px, 340px) minmax(0, 1fr)",
          }}
        >
          <div style={{ display: "grid", gap: 12 }}>
            {researchAssets.map((asset) => (
              <div
                key={asset.id}
                style={{
                  border: asset.id === selectedAssetId ? "1px solid #0f172a" : "1px solid #cbd5e1",
                  borderRadius: 14,
                  display: "grid",
                  gap: 8,
                  padding: 14,
                }}
              >
                <div style={{ alignItems: "center", display: "flex", gap: 8, justifyContent: "space-between" }}>
                  <strong>{asset.title}</strong>
                  <span
                    style={{
                      backgroundColor: "#e2e8f0",
                      borderRadius: 999,
                      fontSize: 12,
                      fontWeight: 700,
                      padding: "4px 10px",
                    }}
                  >
                    v{asset.latest_revision_number}
                  </span>
                </div>
                {asset.latest_report_headline ? (
                  <div style={{ color: "#334155", fontSize: 14 }}>{asset.latest_report_headline}</div>
                ) : null}
                <div style={{ color: "#475569", fontSize: 14 }}>{asset.latest_summary}</div>
                <div style={{ color: "#64748b", fontSize: 12 }}>
                  Updated {new Date(asset.updated_at).toLocaleString()}
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <button onClick={() => onSelectAsset(asset.id)} type="button">
                    Open asset
                  </button>
                  <button onClick={() => onContinueAsset(asset)} type="button">
                    Continue asset
                  </button>
                  {asset.latest_task_id ? (
                    <button onClick={() => onOpenTask(asset.latest_task_id ?? null)} type="button">
                      Open latest run
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>

          <div>
            {!selectedAsset && !isLoadingSelectedAsset ? <p>Select a saved asset to inspect its revision history.</p> : null}
            {isLoadingSelectedAsset && selectedAssetId ? <p>Loading selected asset...</p> : null}
            {selectedAsset ? (
              <div style={{ display: "grid", gap: 16 }}>
                <div
                  style={{
                    backgroundColor: "#f8fafc",
                    border: "1px solid #cbd5e1",
                    borderRadius: 16,
                    display: "grid",
                    gap: 8,
                    padding: 16,
                  }}
                >
                  <div style={{ color: "#475569", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>
                    Workbench asset
                  </div>
                  <h3 style={{ margin: 0 }}>{selectedAsset.title}</h3>
                  <div>
                    <strong>Asset ID:</strong> {selectedAsset.id}
                  </div>
                  <div>
                    <strong>Latest revision:</strong> v{selectedAsset.latest_revision_number}
                  </div>
                  {selectedAsset.latest_report_headline ? (
                    <div>
                      <strong>Latest report:</strong> {selectedAsset.latest_report_headline}
                    </div>
                  ) : null}
                  <p style={{ margin: 0 }}>{selectedAsset.latest_summary}</p>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <button onClick={() => onContinueAsset(selectedAsset)} type="button">
                      Continue from latest revision
                    </button>
                    {selectedAsset.latest_task_id ? (
                      <button onClick={() => onOpenTask(selectedAsset.latest_task_id ?? null)} type="button">
                        Open latest task result
                      </button>
                    ) : null}
                  </div>
                </div>

                <div>
                  <strong>Revision history</strong>
                  {selectedAsset.revisions.length > 0 ? (
                    <ul style={{ display: "grid", gap: 12, listStyle: "none", margin: "12px 0 0", padding: 0 }}>
                      {selectedAsset.revisions.map((revision) => (
                        <li
                          key={revision.id}
                          style={{
                            border: "1px solid #cbd5e1",
                            borderRadius: 14,
                            display: "grid",
                            gap: 8,
                            padding: 14,
                          }}
                        >
                          <div style={{ alignItems: "center", display: "flex", gap: 8, justifyContent: "space-between" }}>
                            <strong>Revision {revision.revision_number}</strong>
                            <span style={{ color: "#64748b", fontSize: 12 }}>
                              {new Date(revision.created_at).toLocaleString()}
                            </span>
                          </div>
                          <div>{revision.summary}</div>
                          {revision.report_headline ? (
                            <div style={{ color: "#334155", fontSize: 14 }}>{revision.report_headline}</div>
                          ) : null}
                          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                            <button onClick={() => onOpenTask(revision.task_id)} type="button">
                              Open task result
                            </button>
                            <button onClick={() => onContinueRevision(selectedAsset, revision)} type="button">
                              Continue from this revision
                            </button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No revisions have been recorded for this asset yet.</p>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </SectionCard>
  );
}
