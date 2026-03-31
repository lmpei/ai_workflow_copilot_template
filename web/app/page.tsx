import type { CSSProperties } from "react";
import Link from "next/link";

const pageStyle: CSSProperties = {
  background:
    "radial-gradient(circle at top left, rgba(14,116,144,0.18), transparent 26%), radial-gradient(circle at top right, rgba(15,23,42,0.18), transparent 22%), linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)",
  minHeight: "100vh",
  padding: "18px 0 24px",
};

const shellStyle: CSSProperties = {
  display: "grid",
  gap: 18,
  margin: "0 auto",
  maxWidth: 1240,
  padding: "0 20px",
};

const heroGridStyle: CSSProperties = {
  alignItems: "stretch",
  display: "grid",
  gap: 18,
  gridTemplateColumns: "minmax(0, 1.12fr) minmax(320px, 0.88fr)",
};

const heroStyle: CSSProperties = {
  background: "linear-gradient(145deg, rgba(15,23,42,0.98) 0%, rgba(8,47,73,0.96) 60%, rgba(14,116,144,0.92) 100%)",
  border: "1px solid rgba(148,163,184,0.26)",
  borderRadius: 32,
  boxShadow: "0 36px 72px rgba(15,23,42,0.22)",
  color: "#f8fafc",
  display: "grid",
  gap: 20,
  padding: "28px 30px",
};

const projectCardStyle: CSSProperties = {
  background: "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,1) 100%)",
  border: "1px solid #dbe4f0",
  borderRadius: 26,
  boxShadow: "0 24px 48px rgba(15,23,42,0.07)",
  display: "grid",
  gap: 16,
  padding: 24,
};

const badgeStyle: CSSProperties = {
  alignItems: "center",
  backgroundColor: "rgba(255,255,255,0.12)",
  border: "1px solid rgba(255,255,255,0.14)",
  borderRadius: 999,
  color: "#e2e8f0",
  display: "inline-flex",
  fontSize: 12,
  fontWeight: 700,
  letterSpacing: "0.08em",
  padding: "5px 10px",
  textTransform: "uppercase",
};

const primaryLinkStyle: CSSProperties = {
  alignItems: "center",
  backgroundColor: "#f8fafc",
  borderRadius: 999,
  color: "#0f172a",
  display: "inline-flex",
  fontWeight: 800,
  justifyContent: "center",
  minHeight: 44,
  padding: "0 18px",
  textDecoration: "none",
};

const secondaryLinkStyle: CSSProperties = {
  alignItems: "center",
  border: "1px solid rgba(255,255,255,0.22)",
  borderRadius: 999,
  color: "#f8fafc",
  display: "inline-flex",
  fontWeight: 700,
  justifyContent: "center",
  minHeight: 44,
  padding: "0 18px",
  textDecoration: "none",
};

const statGridStyle: CSSProperties = {
  display: "grid",
  gap: 12,
  gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
};

const statCardStyle: CSSProperties = {
  backgroundColor: "rgba(255,255,255,0.08)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 18,
  display: "grid",
  gap: 6,
  padding: "14px 16px",
};

const projectTagStyle: CSSProperties = {
  backgroundColor: "#e2e8f0",
  borderRadius: 999,
  color: "#334155",
  display: "inline-flex",
  fontSize: 12,
  fontWeight: 700,
  letterSpacing: "0.04em",
  padding: "4px 10px",
};

export default function HomePage() {
  return (
    <main style={pageStyle}>
      <div style={shellStyle}>
        <section style={heroGridStyle}>
          <article style={heroStyle}>
            <div style={{ display: "grid", gap: 10, maxWidth: 760 }}>
              <span style={badgeStyle}>LMPAI</span>
              <h1 style={{ fontSize: "clamp(2.9rem, 6vw, 5rem)", lineHeight: 0.94, margin: 0 }}>Linminpei</h1>
              <p style={{ color: "#dbeafe", fontSize: 17, lineHeight: 1.75, margin: 0 }}>
                我在做可公开展示、可持续迭代的 AI 产品原型，重点关注 workflow、workbench、eval，
                以及怎样把复杂系统做成真正能被人理解和使用的产品。
              </p>
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
              <Link href="#projects" style={primaryLinkStyle}>
                查看项目
              </Link>
              <Link href="/app" style={secondaryLinkStyle}>
                打开当前项目
              </Link>
            </div>

            <div style={statGridStyle}>
              <article style={statCardStyle}>
                <div style={{ color: "#bae6fd", fontSize: 12 }}>关注方向</div>
                <strong>Workflow / Workbench / Eval</strong>
              </article>
              <article style={statCardStyle}>
                <div style={{ color: "#bae6fd", fontSize: 12 }}>当前重点</div>
                <strong>让 AI 系统更易理解、更可展示</strong>
              </article>
              <article style={statCardStyle}>
                <div style={{ color: "#bae6fd", fontSize: 12 }}>站点结构</div>
                <strong>个人主页 + 项目目录</strong>
              </article>
            </div>
          </article>

          <article id="projects" style={projectCardStyle}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              <span style={projectTagStyle}>当前公开项目</span>
              <span style={projectTagStyle}>Workspace</span>
              <span style={projectTagStyle}>Research Workflow</span>
            </div>
            <div style={{ display: "grid", gap: 8 }}>
              <strong style={{ color: "#0f172a", fontSize: 30 }}>LMPAI Loom</strong>
              <p style={{ color: "#334155", lineHeight: 1.75, margin: 0 }}>
                一个围绕资料、对话、分析、正式输出组织起来的 AI 研究工作台。
              </p>
            </div>
            <div style={{ color: "#475569", display: "grid", gap: 8, lineHeight: 1.75 }}>
              <div>Research Assistant、Support Copilot、Job Assistant 共用同一套 workspace 机制。</div>
              <div>当前重点是研究工作流页面、conversation-first workbench 与公开展示体验。</div>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
              <Link href="/app" style={{ ...primaryLinkStyle, backgroundColor: "#0f172a", color: "#f8fafc" }}>
                进入项目
              </Link>
              <Link
                href="/login"
                style={{ ...primaryLinkStyle, backgroundColor: "#ffffff", border: "1px solid #cbd5e1" }}
              >
                登录后继续
              </Link>
            </div>
          </article>
        </section>
      </div>
    </main>
  );
}
