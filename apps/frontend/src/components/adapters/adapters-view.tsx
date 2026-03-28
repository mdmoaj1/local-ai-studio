"use client";

import type { UseMutationResult, UseQueryResult } from "@tanstack/react-query";
import { Plug, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatBytes } from "@/lib/format";
import type { AdapterDto } from "@/types/finetune";

export type AdaptersViewProps = {
  query: UseQueryResult<AdapterDto[], Error>;
  deleteMutation: UseMutationResult<{ ok: boolean }, Error, number>;
  loadMutation: UseMutationResult<{ ok: boolean }, Error, number>;
};

export function AdaptersView({ query, deleteMutation, loadMutation }: AdaptersViewProps) {
  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Adapters</h1>
        <p className="text-sm text-muted-foreground">
          LoRA checkpoints under <span className="font-mono text-xs">models/adapters/</span>. Load onto the
          active base model from the Models page first (<span className="font-mono text-xs">POST /llm/load</span>
          ), then attach an adapter here.
        </p>
      </div>

      <Card className="border-border/80 bg-card/50 shadow-sm">
        <CardHeader>
          <CardTitle className="text-base">Installed adapters</CardTitle>
          <CardDescription>
            {query.isLoading ? "Loading…" : `${query.data?.length ?? 0} adapter(s)`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.isError ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : (
            <ul className="divide-y divide-border rounded-md border border-border/80">
              {(query.data ?? []).map((a) => (
                <li
                  key={a.id}
                  className="flex flex-wrap items-center justify-between gap-4 px-4 py-3 text-sm hover:bg-muted/40"
                >
                  <div className="min-w-0 flex-1">
                    <div className="font-medium">{a.name}</div>
                    <div className="text-xs text-muted-foreground">
                      Base: {a.base_model} · {formatBytes(a.size)}
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      disabled={loadMutation.isPending}
                      onClick={() => void loadMutation.mutateAsync(a.id)}
                    >
                      <Plug className="mr-1.5 h-3.5 w-3.5" />
                      Load
                    </Button>
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      className="text-muted-foreground hover:text-destructive"
                      disabled={deleteMutation.isPending}
                      onClick={() => void deleteMutation.mutateAsync(a.id)}
                      aria-label={`Delete ${a.name}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
          {loadMutation.isError ? (
            <p className="mt-3 text-sm text-destructive">{loadMutation.error.message}</p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
