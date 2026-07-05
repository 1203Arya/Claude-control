import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Claude Remote",
  description: "Approve or deny Claude Code permission prompts remotely from your phone.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
