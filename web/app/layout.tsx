import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "LMPAI Weave",
  description: "LMPAI Weave 产品工作台。",
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
