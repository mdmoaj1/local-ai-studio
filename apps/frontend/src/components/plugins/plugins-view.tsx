"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { usePluginsQuery, useSetPluginEnabledMutation } from "@/hooks/use-plugins";
import type { PluginDto } from "@/types/plugins";

function PluginRow({
  plugin,
  onToggle,
  pending,
}: {
  plugin: PluginDto;
  onToggle: (id: number, enabled: boolean) => void;
  pending: boolean;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-background/50 p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-semibold">{plugin.title}</span>
          <Badge variant="outline" className="font-mono text-[10px]">
            {plugin.name}
          </Badge>
          {plugin.enabled ? (
            <Badge variant="default">Enabled</Badge>
          ) : (
            <Badge variant="secondary">Disabled</Badge>
          )}
        </div>
        <p className="text-sm text-muted-foreground">{plugin.description}</p>
        <p className="truncate font-mono text-xs text-muted-foreground">{plugin.path}</p>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <span className="text-xs text-muted-foreground">Active</span>
        <Switch
          checked={plugin.enabled}
          disabled={pending}
          onCheckedChange={(v) => onToggle(plugin.id, v)}
        />
      </div>
    </div>
  );
}

export function PluginsView() {
  const pluginsQuery = usePluginsQuery();
  const toggleMutation = useSetPluginEnabledMutation();

  const handleToggle = (id: number, enabled: boolean) => {
    toggleMutation.mutate({ id, enabled });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generator plugins</CardTitle>
        <CardDescription>
          Engine plugins under <span className="font-mono text-xs">engine/plugins/</span>; registry stored in SQLite.
        </CardDescription>
      </CardHeader>
      <Separator />
      <CardContent className="pt-5">
        {pluginsQuery.isLoading ? (
          <div className="text-sm text-muted-foreground">Loading plugins…</div>
        ) : pluginsQuery.isError ? (
          <div className="text-sm text-amber-200">Could not load plugins.</div>
        ) : pluginsQuery.data.length === 0 ? (
          <div className="text-sm text-muted-foreground">No plugins registered. Sync runs on API startup.</div>
        ) : (
          <ScrollArea className="h-[min(560px,70vh)] pr-3">
            <div className="grid gap-3">
              {pluginsQuery.data.map((p) => (
                <PluginRow
                  key={p.id}
                  plugin={p}
                  onToggle={handleToggle}
                  pending={toggleMutation.isPending}
                />
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
