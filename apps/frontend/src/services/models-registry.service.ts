import { apiGetJson, apiPostJson } from "@/services/api-client";
import type { MergedModelDto, RegistryModelDto, StudioModelDto, StudioModelKind } from "@/types/models";

// ---------------------------------------------------------------------------
// Installed / DB-backed models (existing)
// ---------------------------------------------------------------------------

export async function fetchModels(): Promise<StudioModelDto[]> {
  return apiGetJson<StudioModelDto[]>("/api/v1/models");
}

export type AddModelInput = {
  name: string;
  hf_repo_id: string;
  type: StudioModelKind;
  runtime?: string;
  revision?: string | null;
};

export async function addModel(input: AddModelInput): Promise<StudioModelDto> {
  return apiPostJson<StudioModelDto>("/api/v1/models/add", input);
}

export async function startModelDownload(modelId: number, revision?: string | null): Promise<StudioModelDto> {
  return apiPostJson<StudioModelDto>("/api/v1/models/download", { model_id: modelId, revision: revision ?? null });
}

export async function deleteModel(modelId: number): Promise<void> {
  await apiPostJson<{ ok: boolean }>("/api/v1/models/delete", { model_id: modelId });
}

// ---------------------------------------------------------------------------
// Registry endpoints (new)
// ---------------------------------------------------------------------------

export async function fetchAvailableModels(): Promise<RegistryModelDto[]> {
  return apiGetJson<RegistryModelDto[]>("/api/v1/models/available");
}

export async function fetchInstalledModels(): Promise<StudioModelDto[]> {
  return apiGetJson<StudioModelDto[]>("/api/v1/models/installed");
}

export async function fetchAllModels(): Promise<MergedModelDto[]> {
  return apiGetJson<MergedModelDto[]>("/api/v1/models/all");
}

/** One-click install from registry: register then immediately start download. */
export async function installRegistryModel(entry: RegistryModelDto): Promise<StudioModelDto> {
  const created = await addModel({
    name: entry.name,
    hf_repo_id: entry.hf_repo,
    type: entry.type as StudioModelKind,
    runtime: entry.runtime,
  });
  return startModelDownload(created.id);
}
