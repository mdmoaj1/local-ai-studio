"use client";

import type { UseMutationResult } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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

export type ContentGeneratorViewProps = {
  installedModels: StudioModelDto[];
  enabledPlugins: PluginDto[];
  modelId: string;
  onModelIdChange: (value: string) => void;
  pluginId: string;
  onPluginIdChange: (value: string) => void;
  maxTokens: number;
  onMaxTokensChange: (value: number) => void;
  prompt: string;
  onPromptChange: (value: string) => void;
  result: string;
  streaming: boolean;
  streamError: string | null;
  onStream: () => void;
  stubMutation: UseMutationResult<string, Error, void, unknown>;
  onClear: () => void;
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
  streamError,
  onStream,
  stubMutation,
  onClear,
}: ContentGeneratorViewProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Generate</CardTitle>
          <CardDescription>
            Stream tokens over <span className="font-mono text-xs">/ws/generate</span> (queued like REST). Optional
            plugin rewrites your prompt before the LLM.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-2">
            <Label>Installed model</Label>
            <Select value={modelId || undefined} onValueChange={onModelIdChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select model id…" />
              </SelectTrigger>
              <SelectContent>
                {installedModels.map((m) => (
                  <SelectItem key={m.id} value={String(m.id)}>
                    {m.name} (#{m.id})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">Load the model first from the API or Models workflow.</p>
          </div>

          <div className="grid gap-2">
            <Label>Plugin</Label>
            <Select value={pluginId} onValueChange={onPluginIdChange}>
              <SelectTrigger>
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

          <div className="grid gap-2">
            <Label htmlFor="max-tok">Max new tokens</Label>
            <Input
              id="max-tok"
              type="number"
              min={1}
              max={4096}
              value={maxTokens}
              onChange={(e) => onMaxTokensChange(Number(e.target.value) || 256)}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="prompt">Prompt</Label>
            <Textarea
              id="prompt"
              value={prompt}
              onChange={(e) => onPromptChange(e.target.value)}
              placeholder="Describe what you want the model to produce…"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={onStream} disabled={streaming || stubMutation.isPending}>
              {streaming ? "Streaming…" : "Stream (LLM)"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => stubMutation.mutate()}
              disabled={streaming || stubMutation.isPending}
            >
              {stubMutation.isPending ? "Stub…" : "Stub generate"}
            </Button>
            <Button type="button" variant="outline" onClick={onClear} disabled={streaming || stubMutation.isPending}>
              Clear output
            </Button>
          </div>

          {streamError ? <div className="text-sm text-amber-200">{streamError}</div> : null}
          {stubMutation.isError ? <div className="text-sm text-amber-200">Stub generation failed.</div> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Result</CardTitle>
          <CardDescription>Live tokens append here during streaming.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="min-h-[320px] whitespace-pre-wrap rounded-lg border border-border bg-background/40 p-4 font-mono text-sm leading-relaxed text-foreground">
            {result ? result : <span className="text-muted-foreground">No output yet.</span>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
