import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "LMPAI Loom",
  description: "Linminpei 的个人主页与 AI 产品入口。",
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="zh-CN">
      <body
        style={{
          backgroundColor: "#f5f7fb",
          color: "#0f172a",
          fontFamily: '"Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif',
          margin: 0,
          minHeight: "100vh",
        }}
      >
        {children}
      </body>
    </html>
  );
}
