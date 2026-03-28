"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addModel,
  deleteModel,
  fetchAllModels,
  fetchModels,
  installRegistryModel,
  startModelDownload,
  type AddModelInput,
} from "@/services/models-registry.service";
import type { MergedModelDto, RegistryModelDto, StudioModelDto } from "@/types/models";

export const MODELS_QUERY_KEY = ["models"] as const;
export const ALL_MODELS_QUERY_KEY = ["models", "all"] as const;

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/** Existing — all DB rows (backward compat). */
export function useModelsQuery() {
  return useQuery({
    queryKey: MODELS_QUERY_KEY,
    queryFn: fetchModels,
    refetchInterval: (query) => {
      const data = query.state.data as StudioModelDto[] | undefined;
      if (!data?.some((m) => m.status === "downloading")) {
        return false;
      }
      return 2500;
    },
  });
}

/** New — merged registry + DB view. */
export function useAllModelsQuery() {
  return useQuery({
    queryKey: ALL_MODELS_QUERY_KEY,
    queryFn: fetchAllModels,
    refetchInterval: (query) => {
      const data = query.state.data as MergedModelDto[] | undefined;
      if (!data?.some((m) => m.status === "downloading")) {
        return false;
      }
      return 2500;
    },
  });
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export function useAddModelMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: AddModelInput) => addModel(input),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: MODELS_QUERY_KEY });
      await qc.invalidateQueries({ queryKey: ALL_MODELS_QUERY_KEY });
    },
  });
}

export function useDownloadModelMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ modelId, revision }: { modelId: number; revision?: string | null }) =>
      startModelDownload(modelId, revision),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: MODELS_QUERY_KEY });
      await qc.invalidateQueries({ queryKey: ALL_MODELS_QUERY_KEY });
    },
  });
}

export function useDeleteModelMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (modelId: number) => deleteModel(modelId),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: MODELS_QUERY_KEY });
      await qc.invalidateQueries({ queryKey: ALL_MODELS_QUERY_KEY });
    },
  });
}

/** One-click install from registry (add + download in one call). */
export function useInstallRegistryModelMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (entry: RegistryModelDto) => installRegistryModel(entry),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: MODELS_QUERY_KEY });
      await qc.invalidateQueries({ queryKey: ALL_MODELS_QUERY_KEY });
    },
  });
}
