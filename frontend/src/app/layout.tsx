import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DevAgent — Autonomous Debugging Runtime",
  description: "A policy-constrained autonomous engineering agent that investigates, patches, and verifies repository bugs inside an isolated sandbox.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body className="min-h-screen bg-canvas text-zinc-100 antialiased selection:bg-blue-500/30 selection:text-white bg-mesh">
        {children}
      </body>
    </html>
  );
}
