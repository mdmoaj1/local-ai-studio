import { apiPostJson } from "@/services/api-client";
import type { JobDto } from "@/types/finetune";

export type FinetuneStartBody = {
  model_id: number;
  dataset_id: number;
  adapter_name: string;
  epochs?: number;
  learning_rate?: number;
};

export function startFinetuneJob(body: FinetuneStartBody): Promise<JobDto> {
  return apiPostJson<JobDto>("/api/v1/finetune/start", {
    model_id: body.model_id,
    dataset_id: body.dataset_id,
    adapter_name: body.adapter_name,
    epochs: body.epochs ?? 1,
    learning_rate: body.learning_rate ?? 2e-4,
  });
}
