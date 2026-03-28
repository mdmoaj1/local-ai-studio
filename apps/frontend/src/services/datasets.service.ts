import { apiGetJson, apiPostForm, apiPostJson } from "@/services/api-client";
import type { DatasetDto } from "@/types/finetune";

export function fetchDatasets(): Promise<DatasetDto[]> {
  return apiGetJson<DatasetDto[]>("/api/v1/datasets");
}

export function uploadDataset(file: File, name?: string): Promise<DatasetDto> {
  const form = new FormData();
  form.append("file", file);
  if (name?.trim()) {
    form.append("name", name.trim());
  }
  return apiPostForm<DatasetDto>("/api/v1/datasets/add", form);
}

export function deleteDataset(id: number): Promise<{ ok: boolean }> {
  return apiPostJson<{ ok: boolean }>("/api/v1/datasets/delete", { id });
}
