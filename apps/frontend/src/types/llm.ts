export type LLMStatusResponse = {
  loaded_model_id: number | null;
  backend: string;
  device: string;
  cuda_available: boolean;
  queue_depth: number;
  busy: boolean;
  memory: Record<string, number>;
};
