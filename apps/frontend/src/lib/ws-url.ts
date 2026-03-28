import { publicEnv } from "@/lib/env";

export function httpBaseToWebSocketBase(httpBase: string): string {
  const b = httpBase.replace(/\/$/, "");
  if (b.startsWith("https://")) {
    return `wss://${b.slice("https://".length)}`;
  }
  if (b.startsWith("http://")) {
    return `ws://${b.slice("http://".length)}`;
  }
  return `ws://${b}`;
}

export function buildWsUrl(path: string): string {
  const base = httpBaseToWebSocketBase(publicEnv.apiBaseUrl);
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}
