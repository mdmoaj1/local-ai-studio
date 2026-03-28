import { buildWsUrl } from "@/lib/ws-url";

export type LlmStreamParams = {
  modelId: number;
  prompt: string;
  maxTokens: number;
  pluginId: number | null;
  onToken: (token: string) => void;
};

export function runLlmGenerateStream(params: LlmStreamParams): Promise<void> {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(buildWsUrl("/ws/generate"));
    let settled = false;

    const finish = (fn: () => void) => {
      if (settled) return;
      settled = true;
      fn();
    };

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          model_id: params.modelId,
          prompt: params.prompt,
          max_tokens: params.maxTokens,
          plugin_id: params.pluginId,
        }),
      );
    };

    ws.onmessage = (event) => {
      try {
        const o = JSON.parse(String(event.data)) as Record<string, unknown>;
        if (typeof o.error === "string") {
          ws.close();
          finish(() => reject(new Error(o.error)));
          return;
        }
        if (o.done === true) {
          ws.close();
          finish(() => resolve());
          return;
        }
        if (typeof o.token === "string") {
          params.onToken(o.token);
        }
      } catch {
        // ignore malformed frames
      }
    };

    ws.onerror = () => {
      finish(() => reject(new Error("WebSocket error")));
    };

    ws.onclose = () => {
      finish(() => resolve());
    };
  });
}
