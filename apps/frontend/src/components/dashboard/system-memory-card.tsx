"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatBytes } from "@/lib/format";
import { useSystemMetricsStore } from "@/stores/system-metrics-store";

export function SystemMemoryCard() {
  const latest = useSystemMetricsStore((s) => s.latest);

  const ramTotal = latest?.ram_total_bytes ?? 0;
  const ramUsed = latest?.ram_used_bytes ?? 0;
  const vramTotal = latest?.vram_total_bytes ?? 0;
  const vramUsed = latest?.vram_used_bytes ?? 0;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle>Memory</CardTitle>
        <CardDescription>Host RAM and GPU VRAM totals from the live system feed.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        <div className="rounded-lg border border-border bg-background/40 px-3 py-2">
          <div className="text-xs text-muted-foreground">System RAM</div>
          <div className="font-mono text-xs tabular-nums">
            {ramTotal > 0 ? (
              <>
                {formatBytes(ramUsed)} / {formatBytes(ramTotal)}
              </>
            ) : (
              "—"
            )}
          </div>
        </div>
        <div className="rounded-lg border border-border bg-background/40 px-3 py-2">
          <div className="text-xs text-muted-foreground">GPU VRAM</div>
          <div className="font-mono text-xs tabular-nums">
            {vramTotal > 0 ? (
              <>
                {formatBytes(vramUsed)} / {formatBytes(vramTotal)}
              </>
            ) : (
              "No discrete GPU reported (or NVML unavailable)"
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
