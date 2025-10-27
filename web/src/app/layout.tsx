import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AgentSentry",
  description: "Tracing and policy enforcement dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="navbar">
          <div className="container-app flex items-center justify-between">
            <div className="flex gap-4 items-center">
              <a href="/" className="text-lg font-semibold">AgentSentry</a>
              <nav className="flex gap-4 text-sm text-gray-600">
                <a href="/">Sessions</a>
                <a href="/rules">Rules</a>
              </nav>
            </div>
            <div className="text-xs text-gray-500">API: {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}</div>
          </div>
        </header>
        <main className="container-app">{children}</main>
      </body>
    </html>
  );
}