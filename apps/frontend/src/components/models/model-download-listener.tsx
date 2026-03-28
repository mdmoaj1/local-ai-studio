"use client";

import { useModelDownloadWebSocket } from "@/hooks/use-model-download-ws";

type ModelDownloadListenerProps = {
  modelId: number;
};

export function ModelDownloadListener({ modelId }: ModelDownloadListenerProps) {
  useModelDownloadWebSocket({ modelId, enabled: true });
  return null;
}
