import { Suspense } from "react";

import WorkspaceCenterPanel from "../components/workspace/workspace-center-panel";

export default function ProductHomePage() {
  return (
    <main
      style={{
        background:
          "radial-gradient(circle at 10% 8%, rgba(191,219,254,0.34), transparent 18%), radial-gradient(circle at 92% 16%, rgba(226,232,240,0.88), transparent 14%), linear-gradient(180deg, #f4f6fa 0%, #f8fafc 32%, #eef2f7 100%)",
        height: "100svh",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "grid",
          gap: 20,
          height: "100%",
          margin: "0 auto",
          maxWidth: 1680,
          padding: "0 56px 0 96px",
        }}
      >
        <Suspense fallback={null}>
          <WorkspaceCenterPanel />
        </Suspense>
      </div>
    </main>
  );
}
