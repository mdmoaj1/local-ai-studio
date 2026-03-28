"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchRecentHistory } from "@/services/catalog.service";

export function useRecentHistoryQuery() {
  return useQuery({
    queryKey: ["catalog", "history"],
    queryFn: fetchRecentHistory,
  });
}
