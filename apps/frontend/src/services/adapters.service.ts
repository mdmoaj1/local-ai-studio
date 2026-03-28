import { apiGetJson, apiPostJson } from "@/services/api-client";
import type { AdapterDto } from "@/types/finetune";

export function fetchAdapters(): Promise<AdapterDto[]> {
  return apiGetJson<AdapterDto[]>("/api/v1/adapters");
}

export function deleteAdapter(id: number): Promise<{ ok: boolean }> {
  return apiPostJson<{ ok: boolean }>("/api/v1/adapters/delete", { id });
}

export function loadAdapterOnRunner(adapterId: number): Promise<{ ok: boolean }> {
  return apiPostJson<{ ok: boolean }>("/api/v1/llm/load_adapter", { adapter_id: adapterId });
}
