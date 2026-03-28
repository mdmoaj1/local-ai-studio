# Electron shell (planned)

This folder will host the Electron main process, preload scripts, and window management.

The packaged app should:

1. Start or attach to the FastAPI backend on `127.0.0.1` (see `../runtime/`).
2. Load the Next.js UI (static export or dev server) with `NEXT_PUBLIC_APP_MODE=desktop`.

No Electron build is included in this repository yet.
