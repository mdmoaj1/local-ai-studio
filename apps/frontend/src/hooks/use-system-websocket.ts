"use client";

import { useEffect, useRef } from "react";

import {
  buildSystemMetricsWebSocketUrl,
  parseSystemMetricsMessage,
} from "@/services/system-websocket.service";
import { useSystemMetricsStore } from "@/stores/system-metrics-store";

const RECONNECT_BASE_MS = 800;
const RECONNECT_MAX_MS = 10_000;

export function useSystemWebSocket(enabled: boolean) {
  const pushSample = useSystemMetricsStore((s) => s.pushSample);
  const setConnected = useSystemMetricsStore((s) => s.setConnected);
  const setLastError = useSystemMetricsStore((s) => s.setLastError);
  const reconnectAttempt = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!enabled) {
      setConnected(false);
      return;
    }

    let stopped = false;

    const cleanupSocket = () => {
      if (wsRef.current) {
        wsRef.current.onopen = null;
        wsRef.current.onmessage = null;
        wsRef.current.onerror = null;
        wsRef.current.onclose = null;
        try {
          wsRef.current.close();
        } catch {
          // ignore
        }
        wsRef.current = null;
      }
    };

    const scheduleReconnect = () => {
      if (stopped) return;
      if (timerRef.current) clearTimeout(timerRef.current);
      const exp = Math.min(
        RECONNECT_MAX_MS,
        RECONNECT_BASE_MS * 2 ** reconnectAttempt.current,
      );
      reconnectAttempt.current += 1;
      timerRef.current = setTimeout(connect, exp);
    };

    const connect = () => {
      if (stopped) return;
      cleanupSocket();
      setLastError(null);

      const url = buildSystemMetricsWebSocketUrl();
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (stopped) return;
        reconnectAttempt.current = 0;
        setConnected(true);
      };

      ws.onmessage = (event) => {
        if (stopped) return;
        const parsed = parseSystemMetricsMessage(String(event.data));
        if (parsed) pushSample(parsed);
      };

      ws.onerror = () => {
        if (stopped) return;
        setLastError("WebSocket error");
      };

      ws.onclose = () => {
        if (stopped) return;
        setConnected(false);
        scheduleReconnect();
      };
    };

    connect();

    return () => {
      stopped = true;
      if (timerRef.current) clearTimeout(timerRef.current);
      cleanupSocket();
      setConnected(false);
    };
  }, [enabled, pushSample, setConnected, setLastError]);
}
