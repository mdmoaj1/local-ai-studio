"use client";

import Link from "next/link";

import { SystemMemoryCard } from "@/components/dashboard/system-memory-card";
import { SystemUsageChart } from "@/components/dashboard/system-usage-chart";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useRecentHistoryQuery } from "@/hooks/use-dashboard-catalog";
import { useModelsQuery } from "@/hooks/use-models";
import { formatBytes } from "@/lib/format";
import { useSystemMetricsStore } from "@/stores/system-metrics-store";

export function DashboardView() {
  const samples = useSystemMetricsStore((s) => s.history);
  const modelsQuery = useModelsQuery();
  const historyQuery = useRecentHistoryQuery();

  return (
    <div className="grid gap-6">
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle>System usage</CardTitle>
            <CardDescription>Live stream from `/ws/system` (CPU, RAM, GPU, VRAM %).</CardDescription>
          </CardHeader>
          <CardContent>
            {samples.length === 0 ? (
              <div className="grid h-[280px] place-items-center rounded-lg border border-dashed border-border text-sm text-muted-foreground">
                Collecting samples…
              </div>
            ) : (
              <SystemUsageChart samples={samples} />
            )}
          </CardContent>
        </Card>

        <div className="flex flex-col gap-4">
          <SystemMemoryCard />
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Quick actions</CardTitle>
              <CardDescription>Jump into the workflows you use most.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-2">
              <Button asChild variant="secondary" className="justify-start">
                <Link href="/content-generator">Open Content Generator</Link>
              </Button>
              <Button asChild variant="secondary" className="justify-start">
                <Link href="/models">Manage models</Link>
              </Button>
              <Button asChild variant="secondary" className="justify-start">
                <Link href="/plugins">Plugins</Link>
              </Button>
              <Button asChild variant="secondary" className="justify-start">
                <Link href="/tts">Text to speech</Link>
              </Button>
              <Separator className="my-2" />
              <Button asChild variant="outline" className="justify-start">
                <Link href="/settings">Settings</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>Installed models</CardTitle>
            <CardDescription>Backed by SQLite today; swap to Postgres with `DATABASE_URL`.</CardDescription>
          </CardHeader>
          <CardContent>
            {modelsQuery.isLoading ? (
              <div className="text-sm text-muted-foreground">Loading…</div>
            ) : modelsQuery.isError ? (
              <div className="text-sm text-amber-200">Could not load models. Is the API running?</div>
            ) : modelsQuery.data.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                No models registered yet. Add records via the API or upcoming download flow.
              </div>
            ) : (
              <ScrollArea className="h-[220px] pr-3">
                <div className="grid gap-2">
                  {modelsQuery.data.map((m) => (
                    <div
                      key={m.id}
                      className="flex items-center justify-between gap-3 rounded-lg border border-border bg-background/40 px-3 py-2"
                    >
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium">{m.name}</div>
                        <div className="truncate text-xs text-muted-foreground">{m.hf_repo_id}</div>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-1">
                        <Badge variant="secondary">{m.status.replace("_", " ")}</Badge>
                        <div className="text-xs text-muted-foreground">{formatBytes(m.size)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle>Recent history</CardTitle>
            <CardDescription>Latest generations saved to the local database.</CardDescription>
          </CardHeader>
          <CardContent>
            {historyQuery.isLoading ? (
              <div className="text-sm text-muted-foreground">Loading…</div>
            ) : historyQuery.isError ? (
              <div className="text-sm text-amber-200">Could not load history. Is the API running?</div>
            ) : historyQuery.data.length === 0 ? (
              <div className="text-sm text-muted-foreground">No history yet. Generate content to populate this list.</div>
            ) : (
              <ScrollArea className="h-[220px] pr-3">
                <div className="grid gap-2">
                  {historyQuery.data.map((h) => (
                    <div key={h.id} className="rounded-lg border border-border bg-background/40 px-3 py-2">
                      <div className="flex items-center justify-between gap-2">
                        <div className="truncate text-sm font-medium">
                          {h.prompt.trim().split("\n")[0]?.slice(0, 80) || "Generation"}
                        </div>
                        <Badge variant="outline" className="shrink-0">
                          {h.model_id != null ? `#${h.model_id}` : "—"}
                        </Badge>
                      </div>
                      <div className="mt-1 line-clamp-2 text-xs text-muted-foreground">{h.response || h.prompt}</div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
