import type { Metadata } from "next";
import "./globals.css";
import { ColdStartBanner } from "@/shared/ui";

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
    <html lang="en" suppressHydrationWarning className="h-full">
      <body suppressHydrationWarning className="min-h-full flex flex-col bg-[#F7F7F4] text-[#1F2A44] antialiased">
        {/* Free-tier cold start indicator */}
        <ColdStartBanner />

        {/* Skip to Content Link (A11y requirement) */}
        <nav aria-label="Skip links">
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:bg-white focus:text-[#1F2A44] focus:ring-2 focus:ring-[#0F766E] focus:rounded-lg focus:shadow-md font-semibold text-sm"
          >
            Skip to main content
          </a>
        </nav>

        {/* Global Root Content */}
        <div className="flex-1 flex flex-col">{children}</div>
      </body>
    </html>
  );
}
