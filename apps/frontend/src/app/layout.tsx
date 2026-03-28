import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Inter, JetBrains_Mono } from "next/font/google";

import "./globals.css";

import { AppProviders } from "@/providers/app-providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-geist-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Local AI Studio",
  description: "Local LLM, TTS, and voice cloning workspace",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrainsMono.variable} min-h-dvh bg-background font-sans`} suppressHydrationWarning>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
