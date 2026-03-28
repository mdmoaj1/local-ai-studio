"use client";

import { useMemo, useState } from "react";

import { ModelDownloadListener } from "@/components/models/model-download-listener";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  useAddModelMutation,
  useAllModelsQuery,
  useDeleteModelMutation,
  useDownloadModelMutation,
  useInstallRegistryModelMutation,
} from "@/hooks/use-models";
import { formatBytes, formatThroughput } from "@/lib/format";
import { useDownloadProgressStore } from "@/stores/download-progress-store";
import type { MergedModelDto, RegistryModelDto, StudioModelKind } from "@/types/models";
import { Box, Download, Plus, RefreshCw, Trash2, Zap } from "lucide-react";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

type FilterKind = "all" | "llm" | "tts" | "gguf";

const FILTER_LABELS: Record<FilterKind, string> = {
  all: "All",
  llm: "LLM",
  tts: "TTS",
  gguf: "GGUF",
};

function statusVariant(status: MergedModelDto["status"]): "default" | "secondary" | "outline" | "muted" {
  switch (status) {
    case "installed":   return "default";
    case "downloading": return "secondary";
    case "error":       return "outline";
    default:            return "muted";
  }
}

function runtimeVariant(runtime: string): string {
  switch (runtime) {
    case "transformers": return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    case "gguf":         return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    default:             return "bg-muted text-muted-foreground";
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ModelsView() {
  const allModelsQuery = useAllModelsQuery();
  const addMutation = useAddModelMutation();
  const downloadMutation = useDownloadModelMutation();
  const deleteMutation = useDeleteModelMutation();
  const installMutation = useInstallRegistryModelMutation();
  const byModelId = useDownloadProgressStore((s) => s.byModelId);

  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [hfRepo, setHfRepo] = useState("");
  const [kind, setKind] = useState<StudioModelKind>("llm");
  const [runtime, setRuntime] = useState("transformers");
  const [activeFilter, setActiveFilter] = useState<FilterKind>("all");

  const models = allModelsQuery.data ?? [];

  // Filter by type
  const filtered = useMemo<MergedModelDto[]>(() => {
    if (activeFilter === "all") return models;
    if (activeFilter === "gguf") {
      return models.filter((m) => m.runtime === "gguf" || m.type === "gguf");
    }
    return models.filter((m) => m.type === activeFilter);
  }, [models, activeFilter]);

  // Collect model IDs that are currently downloading (for WS listeners)
  const downloadingIds = useMemo(
    () => models.filter((m) => m.status === "downloading" && m.id !== null).map((m) => m.id as number),
    [models],
  );

  const resetForm = () => {
    setName("");
    setHfRepo("");
    setKind("llm");
    setRuntime("transformers");
  };

  const handleAdd = () => {
    addMutation.mutate(
      { name: name.trim(), hf_repo_id: hfRepo.trim(), type: kind, runtime },
      {
        onSuccess: () => {
          setOpen(false);
          resetForm();
        },
      },
    );
  };

  const handleInstall = (m: MergedModelDto) => {
    const entry: RegistryModelDto = {
      name: m.name,
      hf_repo: m.hf_repo,
      type: m.type,
      runtime: m.runtime,
      description: m.description,
    };
    installMutation.mutate(entry);
  };

  // TypeScript alias
  const canInstall = (m: MergedModelDto) =>
    m.status === "not_installed" && !installMutation.isPending && !downloadMutation.isPending;

  const canDownload = (m: MergedModelDto) =>
    m.id !== null && m.status !== "downloading" && m.status !== "installed";

  const canDelete = (m: MergedModelDto) => m.id !== null && !deleteMutation.isPending;

  return (
    <div className="grid gap-6">
      {downloadingIds.map((id) => (
        <ModelDownloadListener key={id} modelId={id} />
      ))}

      <Card>
        <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <CardTitle>Model Library</CardTitle>
            <CardDescription>
              Curated registry + your custom installs. Downloads use{" "}
              <span className="font-mono text-xs">snapshot_download</span> with live WebSocket progress.
            </CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => void allModelsQuery.refetch()}
              disabled={allModelsQuery.isFetching}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>

            {/* Custom add dialog */}
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild>
                <Button type="button" size="sm">
                  <Plus className="mr-2 h-4 w-4" />
                  Add custom
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Register a Hugging Face model</DialogTitle>
                  <DialogDescription>
                    Registers the entry locally. Download pulls a full repo snapshot via{" "}
                    <span className="font-mono text-xs">snapshot_download</span>.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-2">
                  <div className="grid gap-2">
                    <Label htmlFor="m-name">Display name</Label>
                    <Input
                      id="m-name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Llama 3 8B Instruct"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="m-repo">Hugging Face repo id or URL</Label>
                    <Input
                      id="m-repo"
                      value={hfRepo}
                      onChange={(e) => {
                        const val = e.target.value.trim();
                        // Simple client-side parse for immediate feedback
                        if (val.includes("huggingface.co/")) {
                          const parts = val.split("huggingface.co/")[1].split("/");
                          if (parts.length >= 2) {
                            setHfRepo(`${parts[0]}/${parts[1]}`);
                            return;
                          }
                        }
                        setHfRepo(val);
                      }}
                      placeholder="organization/model-name or full Hugging Face URL"
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="grid gap-2">
                      <Label>Type</Label>
                      <Select value={kind} onValueChange={(v) => setKind(v as StudioModelKind)}>
                        <SelectTrigger id="m-type">
                          <SelectValue placeholder="Model type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="llm">LLM</SelectItem>
                          <SelectItem value="tts">TTS</SelectItem>
                          <SelectItem value="voice">Voice</SelectItem>
                          <SelectItem value="gguf">GGUF</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid gap-2">
                      <Label>Runtime</Label>
                      <Select value={runtime} onValueChange={setRuntime}>
                        <SelectTrigger id="m-runtime">
                          <SelectValue placeholder="Runtime" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="transformers">Transformers</SelectItem>
                          <SelectItem value="gguf">GGUF</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  {addMutation.isError ? (
                    <p className="text-sm text-amber-200">Could not add model. Check inputs and API logs.</p>
                  ) : null}
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    onClick={handleAdd}
                    disabled={addMutation.isPending || !name.trim() || !hfRepo.trim()}
                  >
                    {addMutation.isPending ? "Saving…" : "Save"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>

        {/* Filter tabs */}
        <div className="flex gap-1 border-b border-border px-6 pb-0">
          {(Object.keys(FILTER_LABELS) as FilterKind[]).map((f) => {
            const count =
              f === "all"
                ? models.length
                : f === "gguf"
                ? models.filter((m) => m.runtime === "gguf" || m.type === "gguf").length
                : models.filter((m) => m.type === f).length;
            return (
              <button
                key={f}
                id={`models-filter-${f}`}
                type="button"
                onClick={() => setActiveFilter(f)}
                className={`
                  flex items-center gap-1.5 border-b-2 px-3 py-2.5 text-sm font-medium transition-colors
                  ${activeFilter === f
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"}
                `}
              >
                {FILTER_LABELS[f]}
                <span
                  className={`
                    rounded-full px-1.5 py-0.5 text-[10px] font-semibold
                    ${activeFilter === f ? "bg-primary/15 text-primary" : "bg-muted text-muted-foreground"}
                  `}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        <Separator />

        <CardContent className="pt-5">
          {allModelsQuery.isLoading ? (
            <div className="text-sm text-muted-foreground">Loading registry…</div>
          ) : allModelsQuery.isError ? (
            <div className="text-sm text-amber-200">Could not reach the models API.</div>
          ) : filtered.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              No models match the current filter.
            </div>
          ) : (
            <ScrollArea className="h-[min(600px,72vh)] pr-3">
              <div className="grid gap-3">
                {filtered.map((m, idx) => {
                  const progress = m.id !== null ? byModelId[m.id] : undefined;
                  const pct = Math.min(100, Math.max(0, progress?.progress ?? 0));

                  return (
                    <div
                      key={m.id ?? `registry-${idx}`}
                      id={`model-card-${m.id ?? `r${idx}`}`}
                      className="rounded-xl border border-border bg-background/50 p-4 shadow-panel"
                    >
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                        <div className="min-w-0 flex-1 space-y-2">
                          {/* Name + badges */}
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="truncate text-sm font-semibold tracking-tight">{m.name}</h3>
                            <Badge variant="outline" className="font-mono text-[10px] uppercase">
                              {m.type}
                            </Badge>
                            <span
                              className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium ${runtimeVariant(m.runtime)}`}
                            >
                              <Zap className="h-2.5 w-2.5" />
                              {m.runtime}
                            </span>
                            <Badge variant={statusVariant(m.status)}>
                              {m.status.replace("_", " ")}
                            </Badge>
                          </div>

                          {/* Repo + description */}
                          <p className="truncate font-mono text-xs text-muted-foreground">{m.hf_repo}</p>
                          {m.description && (
                            <p className="text-xs text-muted-foreground">{m.description}</p>
                          )}
                          {m.local_path && (
                            <p className="truncate text-xs text-muted-foreground">{m.local_path}</p>
                          )}

                          {/* Download progress */}
                          {m.status === "downloading" && (
                            <div className="space-y-2 pt-1">
                              <Progress value={pct} className="h-1.5" />
                              <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                                <span>
                                  {formatBytes(progress?.downloaded ?? 0)} /{" "}
                                  {(progress?.total ?? 0) > 0 ? formatBytes(progress?.total ?? 0) : "—"}
                                </span>
                                <span>{formatThroughput(progress?.speed ?? 0)}</span>
                              </div>
                            </div>
                          )}

                          {/* Installed size */}
                          {m.status === "installed" && m.size > 0 && (
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Box className="h-3 w-3" />
                              On disk: {formatBytes(m.size)}
                            </div>
                          )}
                        </div>

                        {/* Action buttons */}
                        <div className="flex shrink-0 flex-wrap gap-2 lg:flex-col lg:items-stretch">
                          {/* One-click Install (registry entry not yet in DB) */}
                          {m.id === null && (
                            <Button
                              id={`model-install-btn-${idx}`}
                              type="button"
                              size="sm"
                              className="gap-2"
                              disabled={!canInstall(m)}
                              onClick={() => handleInstall(m)}
                            >
                              <Download className="h-4 w-4" />
                              Install
                            </Button>
                          )}

                          {/* Download (already in DB, not yet installed) */}
                          {m.id !== null && canDownload(m) && (
                            <Button
                              id={`model-download-btn-${m.id}`}
                              type="button"
                              size="sm"
                              variant="secondary"
                              className="gap-2"
                              disabled={downloadMutation.isPending || m.status === "downloading"}
                              onClick={() => downloadMutation.mutate({ modelId: m.id as number })}
                            >
                              <Download className="h-4 w-4" />
                              Download
                            </Button>
                          )}

                          {/* Delete */}
                          {canDelete(m) && (
                            <Button
                              id={`model-delete-btn-${m.id}`}
                              type="button"
                              size="sm"
                              variant="outline"
                              className="gap-2 text-destructive hover:text-destructive"
                              disabled={deleteMutation.isPending}
                              onClick={() => deleteMutation.mutate(m.id as number)}
                            >
                              <Trash2 className="h-4 w-4" />
                              Delete
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
