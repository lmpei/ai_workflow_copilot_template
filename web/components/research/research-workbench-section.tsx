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
        <strong>目标：</strong> {brief.goal ?? "未指定"}
      </div>
      <div>
        <strong>交付形式：</strong> {brief.deliverable ?? "未指定"}
      </div>
      <div>
        <strong>关注方向</strong>
        <div style={{ marginTop: 8 }}>{renderBadgeList(brief.focus_areas, "没有记录关注方向。")}</div>
      </div>
      <div>
        <strong>关键问题</strong>
        {renderList(brief.key_questions, "没有记录关键问题。")}
      </div>
      <div>
        <strong>约束条件</strong>
        {renderList(brief.constraints, "没有记录约束条件。")}
      </div>
      {brief.continuation_notes ? (
        <div>
          <strong>延续备注：</strong> {brief.continuation_notes}
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
        <strong>版本：</strong> v{side.revision_number}
      </div>
      <div>
        <strong>摘要：</strong> {side.summary}
      </div>
      {side.report_headline ? (
        <div>
          <strong>报告标题：</strong> {side.report_headline}
        </div>
      ) : null}
      {renderBrief(side.brief, `${title} 摘要`)}
      <div>
        <strong>开放问题</strong>
        {renderList(side.open_questions, "没有记录开放问题。")}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
        <span>发现数：{side.findings_count}</span>
        <span>证据数：{side.evidence_count}</span>
        <span>文档数：{side.document_count}</span>
        <span>命中数：{side.match_count}</span>
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
      title="Research 工作台"
      description="持久化的研究资产可以让你重新打开已保存报告、查看版本历史、比较相关工作，并在不丢失 lineage 的情况下继续同一项研究。"
    >
      {isLoadingAssets ? <p>正在加载 Research 工作台...</p> : null}
      {!isLoadingAssets && researchAssets.length === 0 ? (
        <p>还没有保存的研究资产。先保存一次已完成的 Research 运行，才能开始工作台生命周期。</p>
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
                  <strong>摘要目标：</strong> {asset.latest_brief.goal ?? "未指定"}
                </div>
                <div style={{ color: "#64748b", fontSize: 12 }}>
                  更新时间 {new Date(asset.updated_at).toLocaleString()}
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <button onClick={() => onSelectAsset(asset.id)} type="button">
                    打开资产
                  </button>
                  <button onClick={() => onContinueAsset(asset)} type="button">
                    继续此资产
                  </button>
                  {asset.latest_task_id ? (
                    <button onClick={() => onOpenTask(asset.latest_task_id ?? null)} type="button">
                      打开最新运行结果
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>

          <div>
            {!selectedAsset && !isLoadingSelectedAsset ? <p>请选择一个已保存资产来查看版本历史。</p> : null}
            {isLoadingSelectedAsset && selectedAssetId ? <p>正在加载所选资产...</p> : null}
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
                    工作台资产
                  </div>
                  <h3 style={{ margin: 0 }}>{selectedAsset.title}</h3>
                  <div>
                    <strong>资产 ID：</strong> {selectedAsset.id}
                  </div>
                  <div>
                    <strong>最新版本：</strong> v{selectedAsset.latest_revision_number}
                  </div>
                  {selectedAsset.latest_report_headline ? (
                    <div>
                      <strong>最新报告：</strong> {selectedAsset.latest_report_headline}
                    </div>
                  ) : null}
                  <p style={{ margin: 0 }}>{selectedAsset.latest_summary}</p>
                  {renderBrief(selectedAsset.latest_brief, "最新摘要")}
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <button onClick={() => onContinueAsset(selectedAsset)} type="button">
                      基于最新版本继续
                    </button>
                    {selectedAsset.latest_task_id ? (
                      <button onClick={() => onOpenTask(selectedAsset.latest_task_id ?? null)} type="button">
                        打开最新任务结果
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
                    <strong>比较研究资产</strong>
                    <p style={{ color: "#475569", margin: "6px 0 0" }}>
                      将当前资产或它的某个版本与另一个已保存研究资产进行比较，查看摘要、开放问题和证据如何随时间变化。
                    </p>
                  </div>
                  {compareCandidates.length === 0 ? (
                    <p style={{ margin: 0 }}>再保存一个研究资产后即可启用比较。</p>
                  ) : (
                    <>
                      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
                        <label style={{ display: "grid", gap: 6 }}>
                          <span>左侧版本</span>
                          <select
                            onChange={(event) => onSelectSelectedAssetCompareRevision(event.target.value)}
                            value={selectedAssetCompareRevisionId ?? ""}
                          >
                            <option value="">最新版本</option>
                            {selectedAsset.revisions.map((revision) => (
                              <option key={revision.id} value={revision.id}>
                                v{revision.revision_number} - {revision.title}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label style={{ display: "grid", gap: 6 }}>
                          <span>右侧资产</span>
                          <select
                            onChange={(event) => onSelectCompareAsset(event.target.value || null)}
                            value={compareAssetId ?? ""}
                          >
                            <option value="">选择一个资产</option>
                            {compareCandidates.map((asset) => (
                              <option key={asset.id} value={asset.id}>
                                {asset.title}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label style={{ display: "grid", gap: 6 }}>
                          <span>右侧版本</span>
                          <select
                            disabled={!compareAsset}
                            onChange={(event) => onSelectCompareAssetRevision(event.target.value)}
                            value={compareAssetRevisionId ?? ""}
                          >
                            <option value="">最新版本</option>
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
                          {isComparing ? "正在比较..." : "比较资产"}
                        </button>
                      </div>
                    </>
                  )}
                  {comparison ? (
                    <div style={{ display: "grid", gap: 16 }}>
                      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
                        {renderComparisonColumn("左侧", comparison.left)}
                        {renderComparisonColumn("右侧", comparison.right)}
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
                        <strong>比较差异</strong>
                        <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
                          <div>
                            <strong>共同关注方向</strong>
                            <div style={{ marginTop: 8 }}>{renderBadgeList(comparison.diff.shared_focus_areas, "没有共同关注方向。")}</div>
                          </div>
                          <div>
                            <strong>仅左侧关注方向</strong>
                            <div style={{ marginTop: 8 }}>{renderBadgeList(comparison.diff.left_only_focus_areas, "没有仅左侧关注方向。")}</div>
                          </div>
                          <div>
                            <strong>仅右侧关注方向</strong>
                            <div style={{ marginTop: 8 }}>{renderBadgeList(comparison.diff.right_only_focus_areas, "没有仅右侧关注方向。")}</div>
                          </div>
                          <div>
                            <strong>共同关键问题</strong>
                            {renderList(comparison.diff.shared_key_questions, "没有共同关键问题。")}
                          </div>
                          <div>
                            <strong>仅左侧关键问题</strong>
                            {renderList(comparison.diff.left_only_key_questions, "没有仅左侧关键问题。")}
                          </div>
                          <div>
                            <strong>仅右侧关键问题</strong>
                            {renderList(comparison.diff.right_only_key_questions, "没有仅右侧关键问题。")}
                          </div>
                          <div>
                            <strong>共同约束条件</strong>
                            {renderList(comparison.diff.shared_constraints, "没有共同约束条件。")}
                          </div>
                          <div>
                            <strong>仅左侧开放问题</strong>
                            {renderList(comparison.diff.left_only_open_questions, "没有仅左侧开放问题。")}
                          </div>
                          <div>
                            <strong>仅右侧开放问题</strong>
                            {renderList(comparison.diff.right_only_open_questions, "没有仅右侧开放问题。")}
                          </div>
                        </div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
                          <span>摘要变化：{comparison.diff.summary_changed ? "是" : "否"}</span>
                          <span>标题变化：{comparison.diff.report_headline_changed ? "是" : "否"}</span>
                          <span>发现差值：{comparison.diff.finding_count_delta}</span>
                          <span>证据差值：{comparison.diff.evidence_count_delta}</span>
                          <span>文档差值：{comparison.diff.document_count_delta}</span>
                          <span>命中差值：{comparison.diff.match_count_delta}</span>
                        </div>
                      </div>
                    </div>
                  ) : null}
                </div>

                <div>
                  <strong>版本历史</strong>
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
                            <strong>版本 {revision.revision_number}</strong>
                            <span style={{ color: "#64748b", fontSize: 12 }}>
                              {new Date(revision.created_at).toLocaleString()}
                            </span>
                          </div>
                          <div>{revision.summary}</div>
                          <div style={{ color: "#334155", fontSize: 13 }}>
                            <strong>摘要目标：</strong> {revision.brief.goal ?? "未指定"}
                          </div>
                          {revision.report_headline ? (
                            <div style={{ color: "#334155", fontSize: 14 }}>{revision.report_headline}</div>
                          ) : null}
                          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                            <button onClick={() => onOpenTask(revision.task_id)} type="button">
                              打开任务结果
                            </button>
                            <button onClick={() => onContinueRevision(selectedAsset, revision)} type="button">
                              基于此版本继续
                            </button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>这个资产还没有记录任何版本。</p>
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
