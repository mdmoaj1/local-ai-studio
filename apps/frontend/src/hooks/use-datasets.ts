"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { deleteDataset, fetchDatasets, uploadDataset } from "@/services/datasets.service";

export const DATASETS_QUERY_KEY = ["datasets"] as const;

export function useDatasetsQuery() {
  return useQuery({
    queryKey: DATASETS_QUERY_KEY,
    queryFn: fetchDatasets,
  });
}

export function useUploadDatasetMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ file, name }: { file: File; name?: string }) => uploadDataset(file, name),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: DATASETS_QUERY_KEY });
    },
  });
}

export function useDeleteDatasetMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteDataset(id),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: DATASETS_QUERY_KEY });
    },
  });
}
