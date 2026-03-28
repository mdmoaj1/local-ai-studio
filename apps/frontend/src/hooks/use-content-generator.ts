"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo, useState } from "react";

import { useModelsQuery } from "@/hooks/use-models";
import { usePluginsQuery } from "@/hooks/use-plugins";
import { createHistoryEntry } from "@/services/catalog.service";
import { generateContentStub } from "@/services/content-generator.service";
import { runLlmGenerateStream } from "@/services/llm-generate-ws.service";

export function useContentGenerator() {
  const queryClient = useQueryClient();
  const modelsQuery = useModelsQuery();
  const pluginsQuery = usePluginsQuery();

  const [modelId, setModelId] = useState("");
  const [pluginId, setPluginId] = useState("none");
  const [maxTokens, setMaxTokens] = useState(512);
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);

  const installedModels = useMemo(
    () => modelsQuery.data?.filter((m) => m.status === "installed") ?? [],
    [modelsQuery.data],
  );

  const enabledPlugins = useMemo(
    () => pluginsQuery.data?.filter((p) => p.enabled) ?? [],
    [pluginsQuery.data],
  );

  const stubMutation = useMutation({
    mutationFn: async () => generateContentStub({ modelId: modelId || "stub", prompt }),
    onSuccess: async (text) => {
      setResult(text);
      try {
        await createHistoryEntry({
          model_id: null,
          prompt,
          response: text.slice(0, 8000),
        });
        await queryClient.invalidateQueries({ queryKey: ["catalog", "history"] });
      } catch {
        // best-effort
      }
    },
  });

  const runStream = useCallback(async () => {
    if (!prompt.trim()) {
      setStreamError("Enter a prompt.");
      return;
    }
    const mid = Number(modelId);
    if (!Number.isFinite(mid) || mid < 1) {
      setStreamError(
        "Choose an installed model (by id). Load it with POST /api/v1/llm/load before streaming.",
      );
      return;
    }
    setStreamError(null);
    setStreaming(true);
    setResult("");
    const pid = pluginId === "none" ? null : Number(pluginId);
    const pluginPk = pid !== null && Number.isFinite(pid) ? pid : null;
    try {
      await runLlmGenerateStream({
        modelId: mid,
        prompt,
        maxTokens,
        pluginId: pluginPk,
        onToken: (t) => setResult((prev) => prev + t),
      });
      await queryClient.invalidateQueries({ queryKey: ["catalog", "history"] });
    } catch (e) {
      setStreamError(e instanceof Error ? e.message : "Stream failed");
    } finally {
      setStreaming(false);
    }
  }, [maxTokens, modelId, pluginId, prompt, queryClient]);

  return {
    modelsQuery,
    pluginsQuery,
    installedModels,
    enabledPlugins,
    modelId,
    setModelId,
    pluginId,
    setPluginId,
    maxTokens,
    setMaxTokens,
    prompt,
    setPrompt,
    result,
    setResult,
    streaming,
    streamError,
    runStream,
    stubMutation,
  };
}
