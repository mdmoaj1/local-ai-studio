"use client";

import { AlertTriangle, Bot, CheckCircle2, ChevronDown, Loader2, Send, Trash2, X, Zap } from "lucide-react";
import { useRef, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { StudioModelDto } from "@/types/models";
import type { PluginDto } from "@/types/plugins";

type Props = {
  installedModels: StudioModelDto[];
  enabledPlugins: PluginDto[];
  modelId: string;
  onModelIdChange: (v: string) => void;
  pluginId: string;
  onPluginIdChange: (v: string) => void;
  maxTokens: number;
  onMaxTokensChange: (v: number) => void;
  prompt: string;
  onPromptChange: (v: string) => void;
  result: string;
  streaming: boolean;
  isLoadingModel: boolean;
  streamError: string | null;
  onStream: () => void;
  onClear: () => void;
  loadedModelId: number | null;
  hardwareWarning: string | null;
};

export function ContentGeneratorView({
  installedModels,
  enabledPlugins,
  modelId,
  onModelIdChange,
  pluginId,
  onPluginIdChange,
  maxTokens,
  onMaxTokensChange,
  prompt,
  onPromptChange,
  result,
  streaming,
  isLoadingModel,
  streamError,
  onStream,
  onClear,
  loadedModelId,
  hardwareWarning,
}: Props) {
  const outputRef = useRef<HTMLDivElement>(null);
  const [warningDismissed, setWarningDismissed] = useState(false);
  const [prevModelId, setPrevModelId] = useState(modelId);

  // Reset warning dismissed when model changes
  if (modelId !== prevModelId) {
    setPrevModelId(modelId);
    setWarningDismissed(false);
  }

  // Auto-scroll output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [result]);

  const selectedModel = installedModels.find((m) => String(m.id) === modelId);
  const isLoaded = loadedModelId !== null && String(loadedModelId) === modelId;
  const isBusy = isLoadingModel || streaming;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (!isBusy && prompt.trim()) onStream();
    }
  };

  return (
    <div className="flex h-full flex-col gap-4">
      {/* ── Toolbar ─────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-card/60 p-4 backdrop-blur-sm">
        {/* Model picker */}
        <div className="min-w-[220px] flex-1 space-y-1.5">
          <Label className="text-xs font-medium text-muted-foreground">LLM Model</Label>
          <Select value={modelId || undefined} onValueChange={onModelIdChange}>
            <SelectTrigger className="h-9">
              <SelectValue placeholder="Select a model…" />
            </SelectTrigger>
            <SelectContent>
              {installedModels.length === 0 ? (
                <SelectItem value="__none__" disabled>
                  No LLMs installed
                </SelectItem>
              ) : (
                installedModels.map((m) => (
                  <SelectItem key={m.id} value={String(m.id)}>
                    {m.name}
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
        </div>

        {/* Plugin picker */}
        <div className="min-w-[160px] flex-1 space-y-1.5">
          <Label className="text-xs font-medium text-muted-foreground">Plugin</Label>
          <Select value={pluginId} onValueChange={onPluginIdChange}>
            <SelectTrigger className="h-9">
              <SelectValue placeholder="None" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None (raw prompt)</SelectItem>
              {enabledPlugins.map((p) => (
                <SelectItem key={p.id} value={String(p.id)}>
                  {p.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Max tokens */}
        <div className="min-w-[160px] flex-1 space-y-1.5">
          <Label className="text-xs font-medium text-muted-foreground">
            Max tokens — <span className="text-foreground font-semibold">{maxTokens}</span>
          </Label>
          <input
            type="range"
            min={64}
            max={4096}
            step={64}
            value={maxTokens}
            onChange={(e) => onMaxTokensChange(Number(e.target.value))}
            className="w-full accent-primary"
          />
        </div>

        {/* Status badge */}
        <div className="space-y-1.5">
          <Label className="text-xs font-medium text-muted-foreground">Status</Label>
          {isLoadingModel ? (
            <Badge variant="outline" className="flex items-center gap-1.5 text-amber-400 border-amber-400/30">
              <Loader2 className="h-3 w-3 animate-spin" />
              Loading…
            </Badge>
          ) : isLoaded ? (
            <Badge variant="outline" className="flex items-center gap-1.5 text-emerald-400 border-emerald-400/30">
              <CheckCircle2 className="h-3 w-3" />
              Loaded
            </Badge>
          ) : (
            <Badge variant="outline" className="flex items-center gap-1.5 text-muted-foreground">
              <Bot className="h-3 w-3" />
              {selectedModel ? "Not loaded" : "No model"}
            </Badge>
          )}
        </div>
      </div>

      {/* ── Hardware Warning ─────────────────────────────────────── */}
      {hardwareWarning && !warningDismissed && (
        <div className="flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
          <span className="flex-1">{hardwareWarning}</span>
          <button
            onClick={() => setWarningDismissed(true)}
            className="ml-auto shrink-0 rounded p-0.5 hover:bg-amber-500/20 transition-colors"
            aria-label="Dismiss warning"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* ── Main area ───────────────────────────────────────────── */}
      <div className="grid flex-1 gap-4 lg:grid-cols-[1fr_1.2fr]">
        {/* Left: Input */}
        <div className="flex flex-col gap-3 rounded-xl border border-border bg-card/60 p-4 backdrop-blur-sm">
          <Label className="text-sm font-semibold">Prompt</Label>

          <Textarea
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your prompt here… (Ctrl+Enter to generate)"
            className="min-h-[260px] flex-1 resize-none font-mono text-sm leading-relaxed"
            disabled={isBusy}
          />

          <div className="flex items-center gap-2">
            <Button
              onClick={onStream}
              disabled={isBusy || !prompt.trim() || !modelId}
              className="gap-2"
            >
              {isLoadingModel ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading model…
                </>
              ) : streaming ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating…
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4" />
                  Generate
                </>
              )}
            </Button>

            <Button
              variant="outline"
              size="icon"
              onClick={onClear}
              disabled={isBusy}
              title="Clear output"
            >
              <Trash2 className="h-4 w-4" />
            </Button>

            <span className="ml-auto text-xs text-muted-foreground">Ctrl+Enter</span>
          </div>

          {streamError && (
            <div className="flex items-center gap-2 rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
              {streamError}
            </div>
          )}
        </div>

        {/* Right: Output */}
        <div className="flex flex-col rounded-xl border border-border bg-card/60 backdrop-blur-sm overflow-hidden">
          <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
            <Bot className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold">Output</span>
            {streaming && (
              <span className="ml-auto flex items-center gap-1.5 text-xs text-muted-foreground">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
                Streaming
              </span>
            )}
          </div>

          <div
            ref={outputRef}
            className="flex-1 overflow-y-auto p-4 font-mono text-sm leading-relaxed whitespace-pre-wrap text-foreground min-h-[300px]"
          >
            {result || (
              <span className="text-muted-foreground italic">
                Output will appear here as tokens stream in…
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
