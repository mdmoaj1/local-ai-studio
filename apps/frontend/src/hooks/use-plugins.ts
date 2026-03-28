"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchPlugins, setPluginEnabled } from "@/services/plugins.service";

export const PLUGINS_QUERY_KEY = ["plugins"] as const;

export function usePluginsQuery() {
  return useQuery({
    queryKey: PLUGINS_QUERY_KEY,
    queryFn: fetchPlugins,
  });
}

export function useSetPluginEnabledMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) => setPluginEnabled(id, enabled),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: PLUGINS_QUERY_KEY });
    },
  });
}
