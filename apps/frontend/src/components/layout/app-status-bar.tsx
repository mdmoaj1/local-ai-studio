"use client";

import { formatPercent } from "@/lib/format";
import { Separator } from "@/components/ui/separator";
import { useSystemMetricsStore } from "@/stores/system-metrics-store";

type MetricProps = {
  label: string;
  value: number | null;
};

function Metric({ label, value }: MetricProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono text-xs tabular-nums text-foreground">
        {value === null ? "—" : formatPercent(value, 1)}
      </span>
    </div>
  );
}

export function AppStatusBar() {
  const latest = useSystemMetricsStore((s) => s.latest);

  return (
    <footer className="flex h-8 items-center gap-3 border-t border-border bg-card/50 px-3 text-xs backdrop-blur">
      <Metric label="CPU" value={latest?.cpu ?? null} />
      <Separator orientation="vertical" className="h-4" />
      <Metric label="RAM" value={latest?.ram ?? null} />
      <Separator orientation="vertical" className="h-4" />
      <Metric label="GPU" value={latest?.gpu ?? null} />
      <Separator orientation="vertical" className="h-4" />
      <Metric label="VRAM" value={latest?.vram ?? null} />
      <div className="ml-auto text-muted-foreground">/ws/system · ~1s cadence</div>
    </footer>
  );
}
