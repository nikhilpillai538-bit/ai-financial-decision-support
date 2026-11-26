import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth/AuthContext";

export const metadata: Metadata = {
  title: "AI Financial Decision Support System | Premium Fintech Command Center",
  description: "Enterprise-grade Personal Financial Portfolio Management, Deterministic Risk Analytics, and FinBERT-grounded AI Decision Support",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" style={{ colorScheme: "dark" }}>
      <body className="antialiased min-h-screen bg-[#090D16] text-slate-100 selection:bg-cyan-500 selection:text-white">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
