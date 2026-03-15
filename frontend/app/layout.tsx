import type { Metadata } from "next";
import "./globals.css";
import { ClientProviders } from "./components/ClientProviders";

export const metadata: Metadata = {
  title: "ContractSentinel — 证据导向合同审查",
  description: "合同风险审查与证据链展示",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="min-h-screen relative">
        <ClientProviders>{children}</ClientProviders>
      </body>
    </html>
  );
}
