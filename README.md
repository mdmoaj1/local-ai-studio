# Local AI Studio

Offline-first workspace for local LLM, TTS, and voice cloning: **FastAPI** backend, **Next.js** (App Router) frontend, **SQLite** via SQLAlchemy (PostgreSQL-ready), and a separate **`engine/`** package for model runtimes. The UI is built like a desktop tool so it can later load inside **Electron** with the same API client configuration.

## Repository layout

- `apps/backend` — REST (`/api/v1/...`) and WebSocket (`/ws/system`) with layered `api` / `services` / `core` / `db` / `utils`
- `apps/frontend` — Next.js + Tailwind + shadcn-style UI, React Query + Zustand, Recharts
- `engine/` — LLM Transformers runner + runtime façade; TTS / GGUF extension points live alongside
- `models/` — reserved for on-disk weights (see `.gitignore`)
- `docs/` — architecture notes

## Prerequisites

- Python 3.11+ with `pip`
- Node.js 20+ and `npm`

## Backend

```bash
cd apps/backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # or set env vars manually
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- `GET /api/v1/system/metrics` — one-shot CPU/RAM/GPU/VRAM (percent)
- `WebSocket /ws/system` — JSON stream `{ "cpu", "ram", "gpu", "vram" }` (percent, ~1s)
- `GET /api/v1/models` — Hugging Face model registry (SQLite table `models`)
- `POST /api/v1/models/add` — register `{ name, hf_repo_id, type }` (`llm` | `tts` | `voice` | `gguf`)
- `POST /api/v1/models/download` — start `snapshot_download` into `models/<slug>/` (`model_id`, optional `revision`)
- `POST /api/v1/models/delete` — cancel active download if needed, remove files under the managed path, delete row
- `WebSocket /ws/download/{model_id}` — `{ progress, speed, downloaded, total }` while downloading
- `POST /api/v1/llm/load` — load one installed **LLM** (`model_id`); unloads any previous model
- `POST /api/v1/llm/unload` — free GPU/CPU memory
- `POST /api/v1/llm/generate` — `{ model_id, prompt, max_tokens }` → `{ text }` (queued; saves to `history`)
- `GET /api/v1/llm/status` — loaded model, backend, device, CUDA flag, queue depth, memory snapshot
- `GET /api/v1/history` — recent rows from table `history` (`model_id`, `prompt`, `response`)
- `POST /api/v1/history` — manual history append (e.g. stub generator)

## Frontend

```bash
cd apps/frontend
copy .env.example .env.local
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` to the API origin (default `http://127.0.0.1:8000`).

## Monorepo helper (optional)

From the repo root, `npm run dev:frontend` runs the frontend if dependencies are installed under `apps/frontend`.
