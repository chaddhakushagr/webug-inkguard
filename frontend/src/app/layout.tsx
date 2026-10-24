import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Inkguard | Pre-Publication Brand Governance Platform",
  description: "Automated brand governance platform for pre-publication content checks against brand guidelines and facts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full bg-slate-950 text-slate-100">
      <body className={`${inter.className} min-h-full flex flex-col antialiased`}>
        {/* Synthetic Demo Banner (SPEC F-02 invariant) */}
        <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-1.5 text-xs text-amber-300 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="inline-block w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span className="font-semibold uppercase tracking-wider">Demo Environment</span>
            <span className="text-amber-400/80">|</span>
            <span>Synthetic Data Only: Fictional Skincare Brand &quot;Lumo&quot;</span>
          </div>
          <div className="flex items-center space-x-4">
            <span className="hidden sm:inline text-amber-300/80">
              AI Mode: <strong className="text-amber-300 font-mono">MOCK (Boundary Safe)</strong>
            </span>
            <a
              href="/about-ai/"
              className="underline hover:text-amber-200 focus:outline-none focus:ring-1 focus:ring-amber-300"
            >
              Data Boundary Disclosure
            </a>
          </div>
        </div>

        {/* Main Application Container */}
        <div className="flex-1 flex flex-col">{children}</div>
      </body>
    </html>
  );
}
