import { buildWsUrl } from "@/lib/ws-url";

export function buildTrainWebSocketUrl(jobId: number): string {
  return buildWsUrl(`/ws/train/${jobId}`);
}

export type TrainSnapshotMessage = {
  snapshot: true;
  status: string;
  progress: number;
  message: string;
};

export type TrainMetricsMessage = {
  progress: number;
  loss: number;
  step: number;
};

export type TrainLogMessage = {
  log: string;
};

export type TrainDoneMessage = {
  done: true;
  progress?: number;
  loss?: number;
  step?: number;
};

export type TrainErrorMessage = {
  error: string;
};

export type TrainWsMessage =
  | TrainSnapshotMessage
  | TrainMetricsMessage
  | TrainLogMessage
  | TrainDoneMessage
  | TrainErrorMessage;

export function parseTrainWsMessage(raw: string): TrainWsMessage | null {
  try {
    const data = JSON.parse(raw) as unknown;
    if (!data || typeof data !== "object") return null;
    const o = data as Record<string, unknown>;
    if (o.snapshot === true) {
      return {
        snapshot: true,
        status: String(o.status ?? ""),
        progress: Number(o.progress ?? 0),
        message: String(o.message ?? ""),
      };
    }
    if (typeof o.error === "string") {
      return { error: o.error };
    }
    if (o.done === true) {
      return {
        done: true,
        progress: typeof o.progress === "number" ? o.progress : undefined,
        loss: typeof o.loss === "number" ? o.loss : undefined,
        step: typeof o.step === "number" ? o.step : undefined,
      };
    }
    if (typeof o.log === "string") {
      return { log: o.log };
    }
    if (
      typeof o.progress === "number" &&
      typeof o.loss === "number" &&
      typeof o.step === "number"
    ) {
      return { progress: o.progress, loss: o.loss, step: o.step };
    }
    return null;
  } catch {
    return null;
  }
}
