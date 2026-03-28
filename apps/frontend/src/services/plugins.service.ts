import { apiGetJson, apiPatchJson } from "@/services/api-client";
import type { PluginDto } from "@/types/plugins";

export async function fetchPlugins(): Promise<PluginDto[]> {
  return apiGetJson<PluginDto[]>("/api/v1/plugins");
}

export async function setPluginEnabled(pluginId: number, enabled: boolean): Promise<PluginDto> {
  return apiPatchJson<PluginDto>(`/api/v1/plugins/${pluginId}/enabled`, { enabled });
}
