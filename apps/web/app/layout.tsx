import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AION OS",
  description: "AION OS control plane"
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
