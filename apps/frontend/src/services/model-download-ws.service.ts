import { buildWsUrl } from "@/lib/ws-url";
import type { DownloadProgressDto } from "@/types/models";

export function buildModelDownloadWebSocketUrl(modelId: number): string {
  return buildWsUrl(`/ws/download/${modelId}`);
}

export function parseDownloadProgressMessage(raw: string): DownloadProgressDto | null {
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") return null;
    const o = parsed as Record<string, unknown>;
    const progress = Number(o.progress);
    const speed = Number(o.speed);
    const downloaded = Number(o.downloaded);
    const total = Number(o.total);
    if ([progress, speed, downloaded, total].some((n) => Number.isNaN(n))) return null;
    return { progress, speed, downloaded, total };
  } catch {
    return null;
  }
}
