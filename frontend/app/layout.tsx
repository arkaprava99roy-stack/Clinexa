import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/AuthProvider";

export const metadata: Metadata = {
  title: "Clinexa — AI Healthcare Intelligence",
  description:
    "Clinexa is your personal AI health companion. Upload medical reports, understand lab results in plain language, and track health trends over time — securely and privately.",
  keywords: ["health AI", "lab results", "medical reports", "health tracker"],
  openGraph: {
    title: "Clinexa — AI Healthcare Intelligence",
    description: "Understand your health reports with AI-powered insights.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="bg-surface text-slate-100 antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
