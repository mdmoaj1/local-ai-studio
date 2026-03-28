"use client";

import { usePathname } from "next/navigation";

import { mainNav } from "@/config/navigation";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useSystemMetricsStore } from "@/stores/system-metrics-store";

function titleForPath(pathname: string) {
  const hit = mainNav.find((n) => n.href === pathname);
  return hit?.title ?? "Workspace";
}

export function AppTopBar() {
  const pathname = usePathname();
  const connected = useSystemMetricsStore((s) => s.connected);
  const lastError = useSystemMetricsStore((s) => s.lastError);

  return (
    <header className="flex h-12 items-center justify-between border-b border-border bg-background/70 px-4 backdrop-blur">
      <div className="flex min-w-0 items-center gap-3">
        <div className="truncate text-sm font-semibold tracking-tight">{titleForPath(pathname)}</div>
        <Separator orientation="vertical" className="h-5" />
        <div className="hidden text-xs text-muted-foreground md:block">
          REST + WebSocket · SQLite today, PostgreSQL-ready
        </div>
      </div>
      <div className="flex items-center gap-2">
        {lastError ? (
          <Badge variant="outline" className="border-amber-500/40 text-amber-200">
            Metrics degraded
          </Badge>
        ) : null}
        <Badge variant={connected ? "default" : "muted"}>
          {connected ? "Live metrics" : "Connecting…"}
        </Badge>
      </div>
    </header>
  );
}
