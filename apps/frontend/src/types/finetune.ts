export type DatasetDto = {
  id: number;
  name: string;
  path: string;
  size: number;
  created_at: string;
};

export type JobDto = {
  id: number;
  type: string;
  status: string;
  progress: number;
  message: string;
  created_at: string;
};

export type AdapterDto = {
  id: number;
  name: string;
  path: string;
  base_model: string;
  size: number;
  created_at: string;
};
