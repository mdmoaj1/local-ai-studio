"use client";

import type { ReactNode } from "react";

import { AppSidebar } from "@/components/layout/app-sidebar";
import { AppStatusBar } from "@/components/layout/app-status-bar";
import { AppTopBar } from "@/components/layout/app-top-bar";
import { SystemMetricsBridge } from "@/providers/system-metrics-bridge";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <SystemMetricsBridge>
      <div className="flex min-h-dvh flex-col bg-background">
        <AppTopBar />
        <div className="flex min-h-0 flex-1">
          <AppSidebar />
          <main className="min-w-0 flex-1 overflow-y-auto bg-gradient-to-b from-background to-card/20">
            <div className="mx-auto w-full max-w-6xl px-6 py-6">{children}</div>
          </main>
        </div>
        <AppStatusBar />
      </div>
    </SystemMetricsBridge>
  );
}
