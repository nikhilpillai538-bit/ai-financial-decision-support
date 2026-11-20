import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth/AuthContext";

export const metadata: Metadata = {
  title: "AI Financial Decision Support System",
  description: "Personal Financial Portfolio Management, Risk Analytics, and AI Decision Support",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
