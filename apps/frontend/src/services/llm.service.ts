import type { LLMStatusResponse } from "@/types/llm";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function loadLlmModel(modelId: number): Promise<void> {
  const res = await fetch(`${BASE}/api/v1/llm/load`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model_id: modelId }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail ?? `Load failed: ${res.status}`);
  }
}

export async function unloadLlmModel(): Promise<void> {
  const res = await fetch(`${BASE}/api/v1/llm/unload`, { method: "POST" });
  if (!res.ok) throw new Error(`Unload failed: ${res.status}`);
}

export async function getLlmStatus(): Promise<LLMStatusResponse> {
  const res = await fetch(`${BASE}/api/v1/llm/status`);
  if (!res.ok) throw new Error(`Status failed: ${res.status}`);
  return res.json() as Promise<LLMStatusResponse>;
}

export async function hardwareCheck(modelId: number): Promise<{
  ok: boolean;
  warning: string | null;
  free_ram_gb: number;
  free_vram_gb: number;
  model_size_gb: number;
}> {
  const res = await fetch(`${BASE}/api/v1/llm/hardware-check/${modelId}`);
  if (!res.ok) throw new Error(`Hardware check failed: ${res.status}`);
  return res.json();
}
