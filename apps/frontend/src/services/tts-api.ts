/**
 * TTS and Voice API client helpers.
 *
 * Uses the shared api-client primitives so all error handling
 * stays consistent with the rest of the app.
 */

import { apiGetJson, apiPostForm, apiPostJson } from "./api-client";
import { publicEnv } from "@/lib/env";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Voice {
  id: number;
  name: string;
  path: string;
  duration: number;
  created_at: string;
}

export interface TTSGenerateRequest {
  text: string;
  voice_id: number;
  model_id: number;
}

export interface TTSGenerateResponse {
  audio_url: string;
  duration: number;
  history_id: number;
  job_id: string;
}

export interface TTSHistoryItem {
  id: number;
  text: string;
  voice_id: number | null;
  model_id: number | null;
  audio_path: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Voice endpoints
// ---------------------------------------------------------------------------

export function listVoices(): Promise<Voice[]> {
  return apiGetJson<Voice[]>("/api/v1/voices");
}

export async function uploadVoice(name: string, file: File): Promise<Voice> {
  const form = new FormData();
  form.append("name", name);
  form.append("file", file);
  return apiPostForm<Voice>("/api/v1/voices/upload", form);
}

export function deleteVoice(id: number): Promise<{ ok: boolean }> {
  return apiPostJson<{ ok: boolean }>("/api/v1/voices/delete", { id });
}

// ---------------------------------------------------------------------------
// TTS endpoints
// ---------------------------------------------------------------------------

export function generateSpeech(req: TTSGenerateRequest): Promise<TTSGenerateResponse> {
  return apiPostJson<TTSGenerateResponse>("/api/v1/tts/generate", req);
}

export function listTtsHistory(): Promise<TTSHistoryItem[]> {
  return apiGetJson<TTSHistoryItem[]>("/api/v1/tts/history");
}

// ---------------------------------------------------------------------------
// WebSocket helper
// ---------------------------------------------------------------------------

export type TtsProgressCallback = (progress: number) => void;

/**
 * Opens a WebSocket to /ws/tts/{jobId} and calls *onProgress* (0-100)
 * for each message received.
 *
 * Returns a cleanup function that closes the socket.
 */
export function subscribeTtsProgress(
  jobId: string,
  onProgress: TtsProgressCallback,
  onDone?: () => void,
): () => void {
  const wsBase = publicEnv.apiBaseUrl.replace(/^http/, "ws");
  const ws = new WebSocket(`${wsBase}/ws/tts/${jobId}`);

  ws.onmessage = (evt) => {
    try {
      const data = JSON.parse(evt.data as string) as { progress?: number };
      if (typeof data.progress === "number") {
        onProgress(data.progress);
        if (data.progress >= 100) {
          onDone?.();
        }
      }
    } catch {
      // ignore malformed frames
    }
  };

  ws.onerror = () => ws.close();

  return () => ws.close();
}

/** Build a full URL for an audio file returned by the API. */
export function audioFileUrl(audioUrl: string): string {
  if (audioUrl.startsWith("http")) return audioUrl;
  return `${publicEnv.apiBaseUrl}${audioUrl}`;
}
