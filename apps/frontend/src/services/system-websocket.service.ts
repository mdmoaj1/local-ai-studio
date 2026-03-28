import { buildWsUrl } from "@/lib/ws-url";
import type { SystemMetricsPayload } from "@/types/system-metrics";

export function buildSystemMetricsWebSocketUrl(): string {
  return buildWsUrl("/ws/system");
}

function num(v: unknown, fallback: number): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

export function parseSystemMetricsMessage(data: string): SystemMetricsPayload | null {
  try {
    const parsed = JSON.parse(data) as unknown;
    if (!parsed || typeof parsed !== "object") return null;
    const o = parsed as Record<string, unknown>;
    const cpu = num(o.cpu, NaN);
    const ram = num(o.ram, NaN);
    const gpu = num(o.gpu, NaN);
    const vram = num(o.vram, NaN);
    if ([cpu, ram, gpu, vram].some((n) => Number.isNaN(n))) return null;
    return {
      cpu,
      ram,
      gpu,
      vram,
      ram_total_bytes: num(o.ram_total_bytes, 0),
      ram_used_bytes: num(o.ram_used_bytes, 0),
      vram_total_bytes: num(o.vram_total_bytes, 0),
      vram_used_bytes: num(o.vram_used_bytes, 0),
    };
  } catch {
    return null;
  }
}
