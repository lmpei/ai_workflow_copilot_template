import WorkspaceCenterPanel from "../components/workspace/workspace-center-panel";

export default function ProductHomePage() {
  return (
    <main
      style={{
        background:
          "radial-gradient(circle at top right, rgba(14,116,144,0.12), transparent 28%), linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%)",
        minHeight: "100vh",
        padding: "20px 0 36px",
      }}
    >
      <div style={{ display: "grid", gap: 16, margin: "0 auto", maxWidth: 1220, padding: "0 20px" }}>
        <WorkspaceCenterPanel />
      </div>
    </main>
  );
}
