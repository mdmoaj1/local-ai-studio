export type HistoryEntryDto = {
  id: number;
  model_id: number | null;
  prompt: string;
  response: string;
  created_at: string;
};
