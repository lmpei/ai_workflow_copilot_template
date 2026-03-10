import type { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  description?: string;
  children?: ReactNode;
};

export default function SectionCard({
  title,
  description,
  children,
}: SectionCardProps) {
  return (
    <section
      style={{
        border: "1px solid #d4d4d8",
        borderRadius: 12,
        padding: 20,
        marginBottom: 16,
      }}
    >
      <h2 style={{ marginTop: 0 }}>{title}</h2>
      {description ? <p style={{ color: "#52525b" }}>{description}</p> : null}
      {children}
    </section>
  );
}
