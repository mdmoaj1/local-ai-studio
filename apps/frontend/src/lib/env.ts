export type AppMode = "web" | "desktop";

function readAppMode(): AppMode {
  const raw = process.env.NEXT_PUBLIC_APP_MODE?.toLowerCase();
  return raw === "desktop" ? "desktop" : "web";
}

function readPublicApiUrl(): string {
  const mode = readAppMode();
  if (mode === "desktop") {
    const port = process.env.NEXT_PUBLIC_API_PORT ?? "8000";
    return `http://127.0.0.1:${port}`;
  }
  const raw = process.env.NEXT_PUBLIC_API_URL;
  if (raw && raw.length > 0) {
    return raw.replace(/\/$/, "");
  }
  return "http://127.0.0.1:8000";
}

export const publicEnv = {
  appMode: readAppMode(),
  apiBaseUrl: readPublicApiUrl(),
} as const;
