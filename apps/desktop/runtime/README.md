# Desktop runtime (planned)

Use this folder for scripts that launch **uvicorn** (or a frozen Python binary) alongside the UI shell.

Suggested layout later:

- `start-backend.ps1` / `start-backend.sh` — `cd apps/backend && uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Optional process supervisor or health checks before opening Electron.
