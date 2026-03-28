"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useRecentHistoryQuery } from "@/hooks/use-dashboard-catalog";

export default function HistoryPage() {
  const historyQuery = useRecentHistoryQuery();

  return (
    <Card>
      <CardHeader>
        <CardTitle>History</CardTitle>
        <CardDescription>Full timeline of saved generations.</CardDescription>
      </CardHeader>
      <CardContent>
        {historyQuery.isLoading ? (
          <div className="text-sm text-muted-foreground">Loading…</div>
        ) : historyQuery.isError ? (
          <div className="text-sm text-amber-200">Could not load history.</div>
        ) : historyQuery.data.length === 0 ? (
          <div className="text-sm text-muted-foreground">No entries yet.</div>
        ) : (
          <ScrollArea className="h-[520px] pr-3">
            <div className="grid gap-2">
              {historyQuery.data.map((h) => (
                <div key={h.id} className="rounded-xl border border-border bg-background/40 p-4 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="text-sm font-semibold">
                      {h.prompt.trim().split("\n")[0]?.slice(0, 96) || "Generation"}
                    </div>
                    <Badge variant="outline">{h.model_id != null ? `model #${h.model_id}` : "—"}</Badge>
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">{new Date(h.created_at).toLocaleString()}</div>
                  <div className="mt-3 text-sm text-foreground">{h.prompt}</div>
                  <div className="mt-2 text-sm text-muted-foreground">{h.response}</div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
