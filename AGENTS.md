# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Open WebUI is a self-hosted AI chat platform (fork customized as "Findlay Park AI"). It has a **SvelteKit frontend** and a **Python FastAPI backend**.

### Running the application (dev mode)

- **Backend**: `cd backend && bash dev.sh` — starts uvicorn with `--reload` on port **8080**. CORS is pre-configured for the frontend dev server.
- **Frontend**: `npm run dev` — starts Vite dev server on port **5173** with HMR.
- Both must run concurrently for full development experience.
- The first user to sign up becomes the admin (via `POST /api/v1/auths/signup`).

### Key dev commands

| Task | Command |
|------|---------|
| Frontend dev server | `npm run dev` |
| Backend dev server | `cd backend && bash dev.sh` |
| Frontend build | `npm run build` |
| Frontend lint (ESLint) | `npx eslint . --fix` |
| Frontend type check | `npm run check` |
| Backend lint (ruff) | `ruff check backend/` |
| Backend format (ruff) | `ruff format backend/` |
| Frontend tests (vitest) | `npx vitest --passWithNoTests --run` |
| Backend tests (pytest) | `PYTHONPATH=backend:$PYTHONPATH python3 -m pytest backend/open_webui/test/ -q` |

### Gotchas and non-obvious notes

- **Python PATH**: pip installs scripts to `~/.local/bin` — ensure it's on `PATH` (`export PATH="$HOME/.local/bin:$PATH"`).
- **Backend PYTHONPATH**: When running pytest or importing `open_webui` outside uvicorn, set `PYTHONPATH=backend:$PYTHONPATH`.
- **Backend integration tests** require Docker + PostgreSQL (they use `AbstractPostgresTest` from `test.util` which is not present in the repo). These tests are designed for CI. The `test_redis.py` also has an import mismatch with the current code. Expect collection errors if running locally without Docker.
- **Frontend tests**: Currently no test files exist; `vitest --passWithNoTests` exits cleanly.
- **ESLint**: Known crash on `FilePreview.svelte` due to `@typescript-eslint/no-unused-vars` rule with Svelte 5. Pre-existing issue.
- **Pyodide**: `npm run dev` and `npm run build` both call `npm run pyodide:fetch` first, which downloads Pyodide + PyPI wheels into `static/pyodide/`. This is automatic.
- **Embedding model**: On first backend startup, `sentence-transformers/all-MiniLM-L6-v2` (~930 MB) is downloaded from Hugging Face. Subsequent starts use the cached model.
- **No LLM required to start**: The app starts fine without Ollama or an OpenAI API key; models list will be empty but the UI and API work.
- **Database**: SQLite by default at `backend/data/webui.db`. No separate DB service needed for dev.
