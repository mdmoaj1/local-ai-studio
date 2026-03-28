"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { deleteAdapter, fetchAdapters, loadAdapterOnRunner } from "@/services/adapters.service";

export const ADAPTERS_QUERY_KEY = ["adapters"] as const;

export function useAdaptersQuery() {
  return useQuery({
    queryKey: ADAPTERS_QUERY_KEY,
    queryFn: fetchAdapters,
  });
}

export function useDeleteAdapterMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteAdapter(id),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ADAPTERS_QUERY_KEY });
    },
  });
}

export function useLoadAdapterMutation() {
  return useMutation({
    mutationFn: (adapterId: number) => loadAdapterOnRunner(adapterId),
  });
}
