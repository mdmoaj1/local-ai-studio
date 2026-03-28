import { create } from "zustand";

import type { SystemMetricsPayload } from "@/types/system-metrics";

const HISTORY_CAP = 72;

type SystemMetricsState = {
  latest: SystemMetricsPayload | null;
  history: SystemMetricsPayload[];
  connected: boolean;
  lastError: string | null;
  pushSample: (sample: SystemMetricsPayload) => void;
  setConnected: (connected: boolean) => void;
  setLastError: (message: string | null) => void;
};

export const useSystemMetricsStore = create<SystemMetricsState>((set) => ({
  latest: null,
  history: [],
  connected: false,
  lastError: null,
  pushSample: (sample) =>
    set((state) => ({
      latest: sample,
      history: [...state.history, sample].slice(-HISTORY_CAP),
    })),
  setConnected: (connected) => set({ connected }),
  setLastError: (message) => set({ lastError: message }),
}));
