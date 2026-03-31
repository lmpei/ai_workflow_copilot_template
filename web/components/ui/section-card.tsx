import type { CSSProperties, ReactNode } from "react";

type SectionCardProps = {
  title: string;
  description?: string;
  children?: ReactNode;
};

const shellStyle: CSSProperties = {
  background: "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,1) 100%)",
  border: "1px solid rgba(203,213,225,0.9)",
  borderRadius: 24,
  boxShadow: "0 20px 40px rgba(15, 23, 42, 0.07)",
  display: "grid",
  gap: 16,
  padding: 24,
};

export default function SectionCard({ title, description, children }: SectionCardProps) {
  return (
    <section style={shellStyle}>
      <div style={{ display: "grid", gap: 8 }}>
        <h2 style={{ color: "#0f172a", fontSize: 22, lineHeight: 1.12, margin: 0 }}>{title}</h2>
        {description ? <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>{description}</p> : null}
      </div>
      {children}
    </section>
  );
}
