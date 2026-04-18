"use client";

import Link from "next/link";

import type { AiFrontierResearchOutputRecord } from "../../lib/types";

type AiFrontierOutputCardProps = {
  output: AiFrontierResearchOutputRecord | null | undefined;
  title?: string;
};

const sectionStyle = {
  borderTop: "1px solid #e2e8f0",
  display: "grid",
  gap: 10,
  paddingTop: 14,
} as const;

function SourceLinks({
  sourceUrl,
  repoUrl,
  docsUrl,
}: {
  sourceUrl?: string | null;
  repoUrl?: string | null;
  docsUrl?: string | null;
}) {
  const links = [
    sourceUrl ? { href: sourceUrl, label: "官方来源" } : null,
    repoUrl ? { href: repoUrl, label: "仓库" } : null,
    docsUrl ? { href: docsUrl, label: "文档" } : null,
  ].filter(Boolean) as Array<{ href: string; label: string }>;

  if (!links.length) {
    return null;
  }

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
      {links.map((link) => (
        <Link
          href={link.href}
          key={`${link.label}-${link.href}`}
          rel="noreferrer"
          style={{
            color: "#0f172a",
            fontSize: 13,
            fontWeight: 700,
            textDecoration: "none",
          }}
          target="_blank"
        >
          {link.label}
        </Link>
      ))}
    </div>
  );
}

export default function AiFrontierOutputCard({ output, title = "本次热点输出" }: AiFrontierOutputCardProps) {
  if (!output) {
    return null;
  }

  return (
    <section
      style={{
        backgroundColor: "#ffffff",
        border: "1px solid #dbe4f0",
        borderRadius: 22,
        display: "grid",
        gap: 16,
        padding: 18,
      }}
    >
      <div style={{ display: "grid", gap: 6 }}>
        <span
          style={{
            color: "#64748b",
            fontSize: 12,
            fontWeight: 800,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
          }}
        >
          AI Signal Tracker
        </span>
        <strong style={{ color: "#0f172a", fontSize: 18 }}>{title}</strong>
      </div>

      <section style={{ display: "grid", gap: 8 }}>
        <strong style={{ color: "#0f172a" }}>热点摘要</strong>
        <p style={{ color: "#334155", lineHeight: 1.8, margin: 0, whiteSpace: "pre-wrap" }}>{output.frontier_summary}</p>
      </section>

      <section style={sectionStyle}>
        <strong style={{ color: "#0f172a" }}>趋势判断</strong>
        <p style={{ color: "#334155", lineHeight: 1.8, margin: 0, whiteSpace: "pre-wrap" }}>{output.trend_judgment}</p>
      </section>

      {output.themes.length ? (
        <section style={sectionStyle}>
          <strong style={{ color: "#0f172a" }}>主题信号</strong>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {output.themes.map((theme, index) => (
              <span
                key={`${theme.label}-${index}`}
                style={{
                  backgroundColor: "#f1f5f9",
                  borderRadius: 999,
                  color: "#0f172a",
                  fontSize: 13,
                  fontWeight: 700,
                  padding: "6px 10px",
                }}
              >
                {theme.label}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      {output.events.length ? (
        <section style={sectionStyle}>
          <strong style={{ color: "#0f172a" }}>关键事件</strong>
          <div style={{ display: "grid", gap: 12 }}>
            {output.events.map((event, index) => (
              <div
                key={`${event.title}-${index}`}
                style={{
                  borderLeft: "2px solid #cbd5e1",
                  display: "grid",
                  gap: 6,
                  paddingLeft: 12,
                }}
              >
                <strong style={{ color: "#0f172a" }}>{event.title}</strong>
                <p style={{ color: "#334155", lineHeight: 1.7, margin: 0 }}>{event.summary}</p>
                <div style={{ color: "#475569", fontSize: 13, lineHeight: 1.7 }}>
                  <strong style={{ color: "#0f172a" }}>为什么重要：</strong>
                  {event.significance}
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {output.project_cards.length ? (
        <section style={sectionStyle}>
          <strong style={{ color: "#0f172a" }}>项目与框架</strong>
          <div style={{ display: "grid", gap: 14 }}>
            {output.project_cards.map((card, index) => (
              <article
                key={`${card.title}-${index}`}
                style={{
                  backgroundColor: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: 18,
                  display: "grid",
                  gap: 8,
                  padding: 14,
                }}
              >
                <div style={{ display: "grid", gap: 4 }}>
                  <strong style={{ color: "#0f172a", fontSize: 16 }}>{card.title}</strong>
                  <p style={{ color: "#334155", lineHeight: 1.7, margin: 0 }}>{card.summary}</p>
                </div>
                <div style={{ color: "#475569", fontSize: 13, lineHeight: 1.7 }}>
                  <strong style={{ color: "#0f172a" }}>为什么值得跟进：</strong>
                  {card.why_it_matters}
                </div>
                <div style={{ color: "#64748b", fontSize: 13 }}>{card.source_label}</div>
                <SourceLinks docsUrl={card.docs_url} repoUrl={card.repo_url} sourceUrl={card.official_url} />
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {output.reference_sources.length ? (
        <section style={sectionStyle}>
          <strong style={{ color: "#0f172a" }}>参考来源</strong>
          <div style={{ display: "grid", gap: 12 }}>
            {output.reference_sources.map((source, index) => (
              <div
                key={`${source.label}-${index}`}
                style={{
                  alignItems: "baseline",
                  borderBottom: index === output.reference_sources.length - 1 ? "none" : "1px solid #e2e8f0",
                  display: "grid",
                  gap: 4,
                  paddingBottom: index === output.reference_sources.length - 1 ? 0 : 12,
                }}
              >
                <strong style={{ color: "#0f172a" }}>{source.label}</strong>
                <div style={{ color: "#64748b", fontSize: 13 }}>{source.source_kind}</div>
                <Link
                  href={source.url}
                  rel="noreferrer"
                  style={{ color: "#0f172a", fontSize: 13, textDecoration: "none" }}
                  target="_blank"
                >
                  打开原始链接
                </Link>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </section>
  );
}
