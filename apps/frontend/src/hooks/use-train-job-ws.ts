"use client";

import { useEffect, useRef, useState } from "react";

import { buildTrainWebSocketUrl, parseTrainWsMessage } from "@/services/train-ws.service";

export type TrainJobWsState = {
  status: string;
  progress: number;
  lastLoss: number;
  step: number;
  logs: string[];
  lossSeries: { step: number; loss: number }[];
  done: boolean;
  error: string | null;
};

const initial: TrainJobWsState = {
  status: "",
  progress: 0,
  lastLoss: 0,
  step: 0,
  logs: [],
  lossSeries: [],
  done: false,
  error: null,
};

export function useTrainJobWs(jobId: number | null) {
  const [state, setState] = useState<TrainJobWsState>(initial);
  const logsRef = useRef<string[]>([]);
  const seriesRef = useRef<{ step: number; loss: number }[]>([]);

  useEffect(() => {
    logsRef.current = [];
    seriesRef.current = [];
    setState(initial);

    if (jobId === null) {
      return;
    }

    const url = buildTrainWebSocketUrl(jobId);
    const ws = new WebSocket(url);
    const ping = window.setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 20_000);

    ws.onmessage = (event) => {
      const msg = parseTrainWsMessage(String(event.data));
      if (!msg) return;

      if ("snapshot" in msg && msg.snapshot) {
        setState((s) => ({
          ...s,
          status: msg.status,
          progress: msg.progress,
          logs: msg.message ? [...logsRef.current, `[snapshot] ${msg.message}`] : logsRef.current,
        }));
        return;
      }

      if ("error" in msg) {
        setState((s) => ({ ...s, error: msg.error, status: "error" }));
        return;
      }

      if ("done" in msg && msg.done) {
        setState((s) => ({
          ...s,
          done: true,
          status: "done",
          progress: msg.progress ?? s.progress,
          lastLoss: msg.loss ?? s.lastLoss,
          step: msg.step ?? s.step,
        }));
        return;
      }

      if ("log" in msg) {
        logsRef.current = [...logsRef.current, msg.log].slice(-800);
        setState((s) => ({ ...s, logs: [...logsRef.current] }));
        return;
      }

      if ("progress" in msg && "loss" in msg && "step" in msg) {
        seriesRef.current = [...seriesRef.current, { step: msg.step, loss: msg.loss }].slice(-400);
        setState((s) => ({
          ...s,
          progress: msg.progress,
          lastLoss: msg.loss,
          step: msg.step,
          lossSeries: [...seriesRef.current],
        }));
      }
    };

    ws.onerror = () => {
      setState((s) => ({ ...s, error: s.error ?? "WebSocket error" }));
    };

    return () => {
      window.clearInterval(ping);
      ws.onmessage = null;
      ws.onerror = null;
      try {
        ws.close();
      } catch {
        // ignore
      }
    };
  }, [jobId]);

  return state;
}
