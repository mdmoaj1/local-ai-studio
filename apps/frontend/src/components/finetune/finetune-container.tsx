"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { FinetuneView } from "@/components/finetune/finetune-view";
import { ADAPTERS_QUERY_KEY } from "@/hooks/use-adapters";
import { useDatasetsQuery } from "@/hooks/use-datasets";
import { useModelsQuery } from "@/hooks/use-models";
import { useTrainJobWs } from "@/hooks/use-train-job-ws";
import { startFinetuneJob } from "@/services/finetune.service";

export function FinetuneContainer() {
  const qc = useQueryClient();
  const modelsQuery = useModelsQuery();
  const datasetsQuery = useDatasetsQuery();

  const [modelId, setModelId] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [adapterName, setAdapterName] = useState("");
  const [epochs, setEpochs] = useState("1");
  const [learningRate, setLearningRate] = useState("0.0002");
  const [jobId, setJobId] = useState<number | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const train = useTrainJobWs(jobId);

  const installedLlm = useMemo(
    () => (modelsQuery.data ?? []).filter((m) => m.type === "llm" && m.status === "installed"),
    [modelsQuery.data],
  );

  const startMutation = useMutation({
    mutationFn: startFinetuneJob,
    onSuccess: (job) => setJobId(job.id),
  });

  useEffect(() => {
    if (train.done) {
      void qc.invalidateQueries({ queryKey: ADAPTERS_QUERY_KEY });
    }
  }, [train.done, qc]);

  const onStart = () => {
    const mid = Number(modelId);
    const did = Number(datasetId);
    const ep = Number(epochs);
    const lr = Number(learningRate);
    if (!Number.isFinite(mid) || mid < 1) {
      setLocalError("Select a base model.");
      return;
    }
    if (!Number.isFinite(did) || did < 1) {
      setLocalError("Select a dataset.");
      return;
    }
    if (!adapterName.trim()) {
      setLocalError("Enter an adapter name.");
      return;
    }
    if (!Number.isFinite(ep) || ep < 1) {
      setLocalError("Epochs must be at least 1.");
      return;
    }
    if (!Number.isFinite(lr) || lr <= 0) {
      setLocalError("Learning rate must be positive.");
      return;
    }
    setLocalError(null);
    startMutation.mutate({
      model_id: mid,
      dataset_id: did,
      adapter_name: adapterName.trim(),
      epochs: ep,
      learning_rate: lr,
    });
  };

  const startError =
    localError ??
    (startMutation.error instanceof Error
      ? startMutation.error.message
      : startMutation.error
        ? String(startMutation.error)
        : null);

  return (
    <FinetuneView
      installedLlmModels={installedLlm}
      datasets={datasetsQuery.data ?? []}
      modelId={modelId}
      onModelIdChange={setModelId}
      datasetId={datasetId}
      onDatasetIdChange={setDatasetId}
      adapterName={adapterName}
      onAdapterNameChange={setAdapterName}
      epochs={epochs}
      onEpochsChange={setEpochs}
      learningRate={learningRate}
      onLearningRateChange={setLearningRate}
      onStart={onStart}
      startPending={startMutation.isPending}
      startError={startError}
      trainProgress={train.progress}
      trainStatus={train.status}
      trainStep={train.step}
      trainLoss={train.lastLoss}
      trainLogs={train.logs}
      trainLossSeries={train.lossSeries}
      trainDone={train.done}
      trainError={train.error}
    />
  );
}
