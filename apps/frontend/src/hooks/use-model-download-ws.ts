"use client";

import { useEffect, useRef } from "react";

import {
  buildModelDownloadWebSocketUrl,
  parseDownloadProgressMessage,
} from "@/services/model-download-ws.service";
import { useDownloadProgressStore } from "@/stores/download-progress-store";

type UseModelDownloadWsOptions = {
  modelId: number | null;
  enabled: boolean;
};

export function useModelDownloadWebSocket({ modelId, enabled }: UseModelDownloadWsOptions) {
  const setForModel = useDownloadProgressStore((s) => s.setForModel);
  const clearModel = useDownloadProgressStore((s) => s.clearModel);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled || modelId === null) {
      return;
    }

    let ws: WebSocket | null = null;
    let isActive = true;

    const timeout = setTimeout(() => {
      if (!isActive) return;

      const url = buildModelDownloadWebSocketUrl(modelId);
      ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        const parsed = parseDownloadProgressMessage(String(event.data));
        if (parsed) {
          setForModel(modelId, parsed);
        }
      };

      ws.onerror = () => {
        // Keep last known progress
      };
    }, 50);

    return () => {
      isActive = false;
      clearTimeout(timeout);
      if (ws) {
        ws.onmessage = null;
        ws.onerror = null;
        try {
          ws.close();
        } catch {
          // ignore
        }
      }
      wsRef.current = null;
      clearModel(modelId);
    };
  }, [enabled, modelId, setForModel, clearModel]);
}
