# Local AI Studio — architecture

## Monorepo layout

- `apps/frontend` — Next.js (App Router) UI; talks to the API over REST and WebSocket. Designed so the same build can be hosted in a desktop shell (Electron) later.
- `apps/backend` — FastAPI service: REST (`/api/v1/...`) and realtime (`/ws/system`, `/ws/tts/{job_id}`, …).
- `engine/` — Python model/runtime adapters (LLM, TTS, finetune, plugins). Keep heavy ML logic here, not in route handlers.
- `models/` — On-disk model weights and manifests (gitignored artifacts; directory is reserved).

## Backend layers

- `app/api` — HTTP routers, WebSocket endpoints, wiring only.
- `app/services` — Use-cases and orchestration (e.g. system metrics).
- `app/core` — Settings and cross-cutting configuration.
- `app/db` — SQLAlchemy models and async session factory (SQLite today; swap `DATABASE_URL` for PostgreSQL later).
- `app/utils` — Small helpers (e.g. NVML GPU probing).

## Realtime metrics

`GET /api/v1/system/metrics` returns a one-shot snapshot. `WebSocket /ws/system` streams JSON `{ cpu, ram, gpu, vram }` as percentages (0–100) on a fixed interval.

## LLM runner

HTTP surface: `app/api/v1/llm.py` (thin). Orchestration: `app/services/llm_service.py` uses `app/services/scheduler.py` (FIFO queue while the runtime is busy) and `app/core/model_manager.py` (single resident model, path checks, coarse RAM guard, `torch.cuda` probing). Inference: `engine/runtime/model_runtime.py` delegates to `engine/llm/transformers_runner.py` (`AutoModelForCausalLM`). Completed generations are written to the SQL table **`history`** (`model_id`, `prompt`, `response`). GGUF / TTS / voice hooks are reserved on `ModelRuntime`.

## TTS runner

HTTP surface: `app/api/routes_tts.py` (`POST /api/v1/tts/generate`, `GET /api/v1/tts/history`) and `app/api/routes_voices.py` (`GET/POST/DELETE /api/v1/voices`).

Orchestration: `app/services/tts_service.py` lazy-loads the runner, runs inference in `asyncio.to_thread`, and persists results to the **`tts_history`** table. Progress is broadcast via `app/core/tts_progress_hub.py` to subscribers of `WebSocket /ws/tts/{job_id}`.

Inference: `engine/tts/qwen_tts_runner.py` (concrete) implements `engine/tts/base_tts_runner.py` (abstract). The base class is the extension point for future backends (XTTS, Bark, StyleTTS2).

Voice Cloning: reference audio files live in `voices/{name}/audio.{ext}` alongside a `config.json`. The `engine/voice/voice_manager.py` scans and validates them. The `app/services/voice_service.py` owns DB persistence (**`voices`** table) and upload/delete lifecycle. Audio outputs are saved under `outputs/audio/` and served at `/audio/{filename}` via FastAPI `StaticFiles`.

Audio utilities: `engine/audio/audio_utils.py` — `save_audio` (soundfile), `convert_audio`, `get_duration`.

Future-ready hooks: `BaseTTSRunner.capabilities()` advertises `emotion`, `style`, `streaming` flags. These are `False` in the Qwen3 implementation and will be wired through `tts_service.py` → runner as future backends add support.

## Desktop (future)

Serve the Next.js static export or dev server inside Electron; point the API client base URL at `http://127.0.0.1:<port>` provided by the packaged FastAPI/uvicorn process.
