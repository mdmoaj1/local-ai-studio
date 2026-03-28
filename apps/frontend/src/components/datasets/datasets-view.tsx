"use client";

import type { UseMutationResult, UseQueryResult } from "@tanstack/react-query";
import { Trash2, Upload } from "lucide-react";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { formatBytes } from "@/lib/format";
import type { DatasetDto } from "@/types/finetune";

export type DatasetsViewProps = {
  query: UseQueryResult<DatasetDto[], Error>;
  uploadMutation: UseMutationResult<DatasetDto, Error, { file: File; name?: string }>;
  deleteMutation: UseMutationResult<{ ok: boolean }, Error, number>;
};

export function DatasetsView({ query, uploadMutation, deleteMutation }: DatasetsViewProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [displayName, setDisplayName] = useState("");

  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Datasets</h1>
        <p className="text-sm text-muted-foreground">
          Upload JSON, JSONL, or TXT datasets. TXT format: prompt then tab then response per line.
        </p>
      </div>

      <Card className="border-border/80 bg-card/50 shadow-sm">
        <CardHeader>
          <CardTitle className="text-base">Add dataset</CardTitle>
          <CardDescription>Optional display name; otherwise the file name is used.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-end gap-3">
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept=".json,.jsonl,.txt"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) {
                void uploadMutation.mutateAsync({ file: f, name: displayName || undefined }).finally(() => {
                  e.target.value = "";
                });
              }
            }}
          />
          <div className="grid w-full max-w-xs gap-1.5">
            <span className="text-xs font-medium text-muted-foreground">Name (optional)</span>
            <Input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g. my-instructions"
            />
          </div>
          <Button
            type="button"
            variant="secondary"
            disabled={uploadMutation.isPending}
            onClick={() => inputRef.current?.click()}
          >
            <Upload className="mr-2 h-4 w-4" />
            Choose file
          </Button>
          {uploadMutation.isError ? (
            <span className="text-sm text-destructive">{uploadMutation.error.message}</span>
          ) : null}
        </CardContent>
      </Card>

      <Card className="border-border/80 bg-card/50 shadow-sm">
        <CardHeader>
          <CardTitle className="text-base">Library</CardTitle>
          <CardDescription>
            {query.isLoading ? "Loading" : `${query.data?.length ?? 0} datasets`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.isError ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : (
            <ul className="divide-y divide-border rounded-md border border-border/80">
              {(query.data ?? []).map((d) => (
                <li
                  key={d.id}
                  className="flex items-center justify-between gap-4 px-4 py-3 text-sm hover:bg-muted/40"
                >
                  <div>
                    <div className="font-medium">{d.name}</div>
                    <div className="text-xs text-muted-foreground">{formatBytes(d.size)}</div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-destructive"
                    disabled={deleteMutation.isPending}
                    onClick={() => void deleteMutation.mutateAsync(d.id)}
                    aria-label={`Delete ${d.name}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
