import { create } from "zustand";

import type { DownloadProgressDto } from "@/types/models";

type DownloadProgressState = {
  byModelId: Record<number, DownloadProgressDto>;
  setForModel: (modelId: number, payload: DownloadProgressDto) => void;
  clearModel: (modelId: number) => void;
};

export const useDownloadProgressStore = create<DownloadProgressState>((set) => ({
  byModelId: {},
  setForModel: (modelId, payload) =>
    set((state) => ({
      byModelId: { ...state.byModelId, [modelId]: payload },
    })),
  clearModel: (modelId) =>
    set((state) => {
      const next = { ...state.byModelId };
      delete next[modelId];
      return { byModelId: next };
    }),
}));
