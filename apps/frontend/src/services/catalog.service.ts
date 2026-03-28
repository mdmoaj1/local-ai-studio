import { apiGetJson, apiPostJson } from "@/services/api-client";
import type { HistoryEntryDto } from "@/types/catalog";

export async function fetchRecentHistory(): Promise<HistoryEntryDto[]> {
  return apiGetJson<HistoryEntryDto[]>("/api/v1/history");
}

export type CreateHistoryEntryInput = {
  model_id: number | null;
  prompt: string;
  response: string;
};

export async function createHistoryEntry(input: CreateHistoryEntryInput): Promise<HistoryEntryDto> {
  return apiPostJson<HistoryEntryDto>("/api/v1/history", input);
}
