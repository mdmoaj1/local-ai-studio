"use client";

import { Play } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatPercent } from "@/lib/format";
import type { DatasetDto } from "@/types/finetune";
import type { StudioModelDto } from "@/types/models";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type FinetuneViewProps = {
  installedLlmModels: StudioModelDto[];
  datasets: DatasetDto[];
  modelId: string;
  onModelIdChange: (v: string) => void;
  datasetId: string;
  onDatasetIdChange: (v: string) => void;
  adapterName: string;
  onAdapterNameChange: (v: string) => void;
  epochs: string;
  onEpochsChange: (v: string) => void;
  learningRate: string;
  onLearningRateChange: (v: string) => void;
  onStart: () => void;
  startPending: boolean;
  startError: string | null;
  trainProgress: number;
  trainStatus: string;
  trainStep: number;
  trainLoss: number;
  trainLogs: string[];
  trainLossSeries: { step: number; loss: number }[];
  trainDone: boolean;
  trainError: string | null;
};

export function FinetuneView(props: FinetuneViewProps) {
  const {
    installedLlmModels,
    datasets,
    modelId,
    onModelIdChange,
    datasetId,
    onDatasetIdChange,
    adapterName,
    onAdapterNameChange,
    epochs,
    onEpochsChange,
    learningRate,
    onLearningRateChange,
    onStart,
    startPending,
    startError,
    trainProgress,
    trainStatus,
    trainStep,
    trainLoss,
    trainLogs,
    trainLossSeries,
    trainDone,
    trainError,
  } = props;

  const chartData = trainLossSeries.map((p) => ({
    step: p.step,
    loss: Number(p.loss.toFixed(4)),
  }));

  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Finetune</h1>
        <p className="text-sm text-muted-foreground">
          LoRA training runs in a background worker. Metrics stream on the train WebSocket.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-border/80 bg-card/50 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">Job</CardTitle>
            <CardDescription>Base model, dataset, and adapter output name.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid gap-2">
              <span className="text-xs font-medium text-muted-foreground">Base model</span>
              <Select value={modelId || undefined} onValueChange={onModelIdChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose model" />
                </SelectTrigger>
                <SelectContent>
                  {installedLlmModels.map((m) => (
                    <SelectItem key={m.id} value={String(m.id)}>
                      {m.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <span className="text-xs font-medium text-muted-foreground">Dataset</span>
              <Select value={datasetId || undefined} onValueChange={onDatasetIdChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose dataset" />
                </SelectTrigger>
                <SelectContent>
                  {datasets.map((d) => (
                    <SelectItem key={d.id} value={String(d.id)}>
                      {d.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <span className="text-xs font-medium text-muted-foreground">Adapter name</span>
              <Input value={adapterName} onChange={(e) => onAdapterNameChange(e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-2">
                <span className="text-xs font-medium text-muted-foreground">Epochs</span>
                <Input value={epochs} onChange={(e) => onEpochsChange(e.target.value)} type="number" min={1} />
              </div>
              <div className="grid gap-2">
                <span className="text-xs font-medium text-muted-foreground">Learning rate</span>
                <Input value={learningRate} onChange={(e) => onLearningRateChange(e.target.value)} />
              </div>
            </div>
            <Button type="button" disabled={startPending} onClick={onStart}>
              <Play className="mr-2 h-4 w-4" />
              Start training
            </Button>
            {startError ? <p className="text-sm text-destructive">{startError}</p> : null}
          </CardContent>
        </Card>

        <Card className="border-border/80 bg-card/50 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">Progress</CardTitle>
            <CardDescription>
              {trainStatus ? `Status: ${trainStatus}` : "Status: idle"}
              {trainStep > 0 ? ` · step ${trainStep} · loss ${trainLoss.toFixed(4)}` : ""}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid gap-2">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Completion</span>
                <span>{formatPercent(Math.min(100, trainProgress), 0)}</span>
              </div>
              <Progress value={Math.min(100, trainProgress)} className="h-2" />
            </div>
            {trainError ? <p className="text-sm text-destructive">{trainError}</p> : null}
            {trainDone ? <p className="text-sm text-emerald-600 dark:text-emerald-400">Done.</p> : null}
            <div className="grid gap-2">
              <span className="text-xs font-medium text-muted-foreground">Loss</span>
              <div className="h-56 w-full rounded-md border border-border/80 bg-background/40 p-2">
                {chartData.length === 0 ? (
                  <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                    Waiting for training metrics.
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-border/60" />
                      <XAxis dataKey="step" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                      <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" width={44} />
                      <Tooltip
                        contentStyle={{
                          background: "hsl(var(--card))",
                          border: "1px solid hsl(var(--border))",
                          borderRadius: 6,
                          fontSize: 12,
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="loss"
                        stroke="hsl(var(--primary))"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/80 bg-card/50 shadow-sm">
        <CardHeader>
          <CardTitle className="text-base">Logs</CardTitle>
          <CardDescription>GPU memory lines when CUDA is available.</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-64 rounded-md border border-border/80 bg-muted/20 p-3">
            <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-muted-foreground">
              {trainLogs.length === 0 ? "No log lines yet." : trainLogs.join("\n")}
            </pre>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
