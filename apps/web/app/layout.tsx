import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Regulatory-AugSys",
  description:
    "Local-first regulatory evidence and CTD/eCTD CMC readiness tool (internal draft; not submission-validated).",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
