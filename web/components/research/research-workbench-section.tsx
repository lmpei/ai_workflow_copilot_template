import type {
  ResearchAssetComparisonRecord,
  ResearchAssetRecord,
  ResearchAssetRevisionRecord,
  ResearchAssetSummaryRecord,
  ResearchBriefRecord,
} from "../../lib/types";
import SectionCard from "../ui/section-card";

type ResearchWorkbenchSectionProps = {
  researchAssets: ResearchAssetSummaryRecord[];
  selectedAssetId: string | null;
  selectedAsset: ResearchAssetRecord | null;
  compareAssetId: string | null;
  compareAsset: ResearchAssetRecord | null;
  selectedAssetCompareRevisionId: string | null;
  compareAssetRevisionId: string | null;
  comparison: ResearchAssetComparisonRecord | null;
  isLoadingAssets: boolean;
  isLoadingSelectedAsset: boolean;
  isComparing: boolean;
  onSelectAsset: (assetId: string) => void;
  onSelectCompareAsset: (assetId: string | null) => void;
  onSelectSelectedAssetCompareRevision: (revisionId: string) => void;
  onSelectCompareAssetRevision: (revisionId: string) => void;
  onRunComparison: () => void;
  onContinueAsset: (asset: ResearchAssetSummaryRecord | ResearchAssetRecord) => void;
  onContinueRevision: (asset: ResearchAssetRecord, revision: ResearchAssetRevisionRecord) => void;
  onOpenTask: (taskId: string | null) => void;
};

function renderList(items: string[], emptyText: string) {
  if (items.length === 0) {
    return <p style={{ color: "#64748b", margin: 0 }}>{emptyText}</p>;
  }

  return (
    <ul style={{ margin: "8px 0 0", paddingLeft: 18 }}>
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function renderBadgeList(items: string[], emptyText: string) {
  if (items.length === 0) {
    return <p style={{ color: "#64748b", margin: 0 }}>{emptyText}</p>;
  }

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
      {items.map((item) => (
        <span
          key={item}
          style={{
            backgroundColor: "#e2e8f0",
            borderRadius: 999,
            color: "#0f172a",
            fontSize: 12,
            fontWeight: 600,
            padding: "4px 10px",
          }}
        >
          {item}
        </span>
      ))}
    </div>
  );
}

function renderBrief(brief: ResearchBriefRecord, label: string) {
  return (
    <div
      style={{
        backgroundColor: "#f8fafc",
        border: "1px solid #cbd5e1",
        borderRadius: 12,
        display: "grid",
        gap: 10,
        padding: 12,
      }}
    >
      <div style={{ color: "#475569", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>{label}</div>
      <div>
        <strong>Goal:</strong> {brief.goal ?? "Not specified"}
      </div>
      <div>
        <strong>Deliverable:</strong> {brief.deliverable ?? "Not specified"}
      </div>
      <div>
        <strong>Focus areas</strong>
        <div style={{ marginTop: 8 }}>{renderBadgeList(brief.focus_areas, "No focus areas recorded.")}</div>
      </div>
      <div>
        <strong>Key questions</strong>
        {renderList(brief.key_questions, "No key questions recorded.")}
      </div>
      <div>
        <strong>Constraints</strong>
        {renderList(brief.constraints, "No constraints recorded.")}
      </div>
      {brief.continuation_notes ? (
        <div>
          <strong>Continuation notes:</strong> {brief.continuation_notes}
        </div>
      ) : null}
    </div>
  );
}

function renderComparisonColumn(
  title: string,
  side: ResearchAssetComparisonRecord["left"] | ResearchAssetComparisonRecord["right"],
) {
  return (
    <div
      style={{
        border: "1px solid #cbd5e1",
        borderRadius: 14,
        display: "grid",
        gap: 10,
        padding: 14,
      }}
    >
      <div>
        <div style={{ color: "#475569", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>{title}</div>
        <h4 style={{ margin: "6px 0 0" }}>{side.asset_title}</h4>
      </div>
      <div>
        <strong>Revision:</strong> v{side.revision_number}
      </div>
      <div>
        <strong>Summary:</strong> {side.summary}
      </div>
      {side.report_headline ? (
        <div>
          <strong>Report headline:</strong> {side.report_headline}
        </div>
      ) : null}
      {renderBrief(side.brief, `${title} brief`)}
      <div>
        <strong>Open questions</strong>
        {renderList(side.open_questions, "No open questions recorded.")}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
        <span>Findings: {side.findings_count}</span>
        <span>Evidence: {side.evidence_count}</span>
        <span>Documents: {side.document_count}</span>
        <span>Matches: {side.match_count}</span>
      </div>
    </div>
  );
}

export default function ResearchWorkbenchSection({
  researchAssets,
  selectedAssetId,
  selectedAsset,
  compareAssetId,
  compareAsset,
  selectedAssetCompareRevisionId,
  compareAssetRevisionId,
  comparison,
  isLoadingAssets,
  isLoadingSelectedAsset,
  isComparing,
  onSelectAsset,
  onSelectCompareAsset,
  onSelectSelectedAssetCompareRevision,
  onSelectCompareAssetRevision,
  onRunComparison,
  onContinueAsset,
  onContinueRevision,
  onOpenTask,
}: ResearchWorkbenchSectionProps) {
  const compareCandidates = researchAssets.filter((asset) => asset.id !== selectedAssetId);

  return (
    <SectionCard
      title="Research workbench"
      description="Persistent research assets let you reopen a saved report, review revision history, compare related work, and continue the same investigation without losing lineage."
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
                <div style={{ color: "#334155", fontSize: 13 }}>
                  <strong>Brief goal:</strong> {asset.latest_brief.goal ?? "Not specified"}
                </div>
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
                  {renderBrief(selectedAsset.latest_brief, "Latest brief")}
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
                  <div>
                    <strong>Compare research assets</strong>
                    <p style={{ color: "#475569", margin: "6px 0 0" }}>
                      Compare the current asset or one of its revisions against another saved research asset to inspect how the brief, open questions, and evidence changed over time.
                    </p>
                  </div>
                  {compareCandidates.length === 0 ? (
                    <p style={{ margin: 0 }}>Save another research asset to unlock comparison.</p>
                  ) : (
                    <>
                      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
                        <label style={{ display: "grid", gap: 6 }}>
                          <span>Left revision</span>
                          <select
                            onChange={(event) => onSelectSelectedAssetCompareRevision(event.target.value)}
                            value={selectedAssetCompareRevisionId ?? ""}
                          >
                            <option value="">Latest revision</option>
                            {selectedAsset.revisions.map((revision) => (
                              <option key={revision.id} value={revision.id}>
                                v{revision.revision_number} - {revision.title}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label style={{ display: "grid", gap: 6 }}>
                          <span>Right asset</span>
                          <select
                            onChange={(event) => onSelectCompareAsset(event.target.value || null)}
                            value={compareAssetId ?? ""}
                          >
                            <option value="">Select an asset</option>
                            {compareCandidates.map((asset) => (
                              <option key={asset.id} value={asset.id}>
                                {asset.title}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label style={{ display: "grid", gap: 6 }}>
                          <span>Right revision</span>
                          <select
                            disabled={!compareAsset}
                            onChange={(event) => onSelectCompareAssetRevision(event.target.value)}
                            value={compareAssetRevisionId ?? ""}
                          >
                            <option value="">Latest revision</option>
                            {(compareAsset?.revisions ?? []).map((revision) => (
                              <option key={revision.id} value={revision.id}>
                                v{revision.revision_number} - {revision.title}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                        <button disabled={!compareAssetId || isComparing} onClick={onRunComparison} type="button">
                          {isComparing ? "Comparing..." : "Compare assets"}
                        </button>
                      </div>
                    </>
                  )}
                  {comparison ? (
                    <div style={{ display: "grid", gap: 16 }}>
                      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
                        {renderComparisonColumn("Left", comparison.left)}
                        {renderComparisonColumn("Right", comparison.right)}
                      </div>
                      <div
                        style={{
                          border: "1px solid #cbd5e1",
                          borderRadius: 14,
                          display: "grid",
                          gap: 12,
                          padding: 14,
                        }}
                      >
                        <strong>Comparison diff</strong>
                        <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
                          <div>
                            <strong>Shared focus areas</strong>
                            <div style={{ marginTop: 8 }}>{renderBadgeList(comparison.diff.shared_focus_areas, "No shared focus areas.")}</div>
                          </div>
                          <div>
                            <strong>Left-only focus areas</strong>
                            <div style={{ marginTop: 8 }}>{renderBadgeList(comparison.diff.left_only_focus_areas, "No left-only focus areas.")}</div>
                          </div>
                          <div>
                            <strong>Right-only focus areas</strong>
                            <div style={{ marginTop: 8 }}>{renderBadgeList(comparison.diff.right_only_focus_areas, "No right-only focus areas.")}</div>
                          </div>
                          <div>
                            <strong>Shared key questions</strong>
                            {renderList(comparison.diff.shared_key_questions, "No shared key questions.")}
                          </div>
                          <div>
                            <strong>Left-only key questions</strong>
                            {renderList(comparison.diff.left_only_key_questions, "No left-only key questions.")}
                          </div>
                          <div>
                            <strong>Right-only key questions</strong>
                            {renderList(comparison.diff.right_only_key_questions, "No right-only key questions.")}
                          </div>
                          <div>
                            <strong>Shared constraints</strong>
                            {renderList(comparison.diff.shared_constraints, "No shared constraints.")}
                          </div>
                          <div>
                            <strong>Left-only open questions</strong>
                            {renderList(comparison.diff.left_only_open_questions, "No left-only open questions.")}
                          </div>
                          <div>
                            <strong>Right-only open questions</strong>
                            {renderList(comparison.diff.right_only_open_questions, "No right-only open questions.")}
                          </div>
                        </div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
                          <span>Summary changed: {comparison.diff.summary_changed ? "yes" : "no"}</span>
                          <span>Headline changed: {comparison.diff.report_headline_changed ? "yes" : "no"}</span>
                          <span>Findings delta: {comparison.diff.finding_count_delta}</span>
                          <span>Evidence delta: {comparison.diff.evidence_count_delta}</span>
                          <span>Documents delta: {comparison.diff.document_count_delta}</span>
                          <span>Matches delta: {comparison.diff.match_count_delta}</span>
                        </div>
                      </div>
                    </div>
                  ) : null}
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
                          <div style={{ color: "#334155", fontSize: 13 }}>
                            <strong>Brief goal:</strong> {revision.brief.goal ?? "Not specified"}
                          </div>
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
