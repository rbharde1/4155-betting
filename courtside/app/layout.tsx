import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Courtside — NBA Paper Picks",
  description: "Risk-free NBA predictions. Moneyline, spread, totals, and a record you can stand behind.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
