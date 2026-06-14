import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { RedAlertOverlay } from "@/components/alerts/RedAlertOverlay";
import { Providers } from "./providers";
import { AppWrapper } from "@/components/layout/AppWrapper";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "RailMind V3.0",
  description: "Acoustic Railway Intelligence Network — 6-Agent Autonomous Command Center",
  manifest: "/manifest.json",
  appleWebApp: { capable: true, statusBarStyle: "black-translucent", title: "RailMind" },
};

export const viewport = {
  themeColor: "#0a84ff",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} dark`}>
      <body className="bg-[#0a0a0c] text-white antialiased">
        <Providers>
          <AppWrapper>
            {children}
          </AppWrapper>
        </Providers>
      </body>
    </html>
  );
}
