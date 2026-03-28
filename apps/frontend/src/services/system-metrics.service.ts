import { apiGetJson } from "@/services/api-client";
import type { SystemMetricsPayload } from "@/types/system-metrics";

export async function fetchSystemMetricsSnapshot(): Promise<SystemMetricsPayload> {
  return apiGetJson<SystemMetricsPayload>("/api/v1/system/metrics");
}
