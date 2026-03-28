"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo, useState } from "react";

import { useInstalledModelsQuery } from "@/hooks/use-models";
import { usePluginsQuery } from "@/hooks/use-plugins";
import { getLlmStatus, hardwareCheck, loadLlmModel } from "@/services/llm.service";
import { runLlmGenerateStream } from "@/services/llm-generate-ws.service";

export function useContentGenerator() {
  const queryClient = useQueryClient();
  const modelsQuery = useInstalledModelsQuery();
  const pluginsQuery = usePluginsQuery();

  const [modelId, setModelId] = useState("");
  const [pluginId, setPluginId] = useState("none");
  const [maxTokens, setMaxTokens] = useState(512);
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [isLoadingModel, setIsLoadingModel] = useState(false);

  // Only show LLM models in this page
  const installedModels = useMemo(
    () => modelsQuery.data?.filter((m) => m.type === "llm") ?? [],
    [modelsQuery.data],
  );

  const enabledPlugins = useMemo(
    () => pluginsQuery.data?.filter((p) => p.enabled) ?? [],
    [pluginsQuery.data],
  );

  // LLM status — which model is currently loaded
  const llmStatusQuery = useQuery({
    queryKey: ["llm", "status"],
    queryFn: getLlmStatus,
    refetchInterval: 5000,
  });

  const loadedModelId = llmStatusQuery.data?.loaded_model_id ?? null;

  // Hardware capability check for the selected model
  const selectedModelId = Number(modelId);
  const hwCheckQuery = useQuery({
    queryKey: ["llm", "hardware-check", selectedModelId],
    queryFn: () => hardwareCheck(selectedModelId),
    enabled: Number.isFinite(selectedModelId) && selectedModelId > 0,
    staleTime: 30_000,
  });

  const hardwareWarning = hwCheckQuery.data?.warning ?? null;

  const runStream = useCallback(async () => {
    if (!prompt.trim()) {
      setStreamError("Enter a prompt first.");
      return;
    }
    const mid = Number(modelId);
    if (!Number.isFinite(mid) || mid < 1) {
      setStreamError("Select an installed LLM model.");
      return;
    }
    setStreamError(null);
    setResult("");

    // Auto-load model if it's not already the active one
    if (loadedModelId !== mid) {
      try {
        setIsLoadingModel(true);
        await loadLlmModel(mid);
        await queryClient.invalidateQueries({ queryKey: ["llm", "status"] });
      } catch (e) {
        setStreamError(e instanceof Error ? e.message : "Failed to load model.");
        setIsLoadingModel(false);
        return;
      } finally {
        setIsLoadingModel(false);
      }
    }

    const pid = pluginId === "none" ? null : Number(pluginId);
    const pluginPk = pid !== null && Number.isFinite(pid) ? pid : null;

    setStreaming(true);
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
      setStreamError(e instanceof Error ? e.message : "Stream failed.");
    } finally {
      setStreaming(false);
    }
  }, [maxTokens, modelId, pluginId, prompt, queryClient, loadedModelId]);

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
    isLoadingModel,
    loadedModelId,
    hardwareWarning,
    llmStatusQuery,
    hwCheckQuery,
  };
}
