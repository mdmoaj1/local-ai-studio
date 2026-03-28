export type StudioModelKind = "llm" | "tts" | "voice" | "gguf";
export type StudioModelRuntime = "transformers" | "gguf" | "unknown";
export type StudioModelStatus = "not_installed" | "downloading" | "installed" | "error";

/** DB-backed model (installed or in-progress). */
export type StudioModelDto = {
  id: number;
  name: string;
  hf_repo_id: string;
  local_path: string;
  size: number;
  status: StudioModelStatus;
  type: StudioModelKind;
  runtime: StudioModelRuntime;
  created_at: string;
};

/** Entry from registry.json (no DB row). */
export type RegistryModelDto = {
  name: string;
  hf_repo: string;
  type: string;
  runtime: string;
  description: string;
};

/** Outer-join of registry + DB: what the /all endpoint returns. */
export type MergedModelDto = {
  name: string;
  hf_repo: string;
  type: string;
  runtime: string;
  description: string;
  // null when not yet added to DB
  id: number | null;
  status: StudioModelStatus;
  size: number;
  local_path: string;
};

export type DownloadProgressDto = {
  progress: number;
  speed: number;
  downloaded: number;
  total: number;
  status?: string;
};
