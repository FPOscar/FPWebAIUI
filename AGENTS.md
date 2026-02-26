# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Open WebUI (v0.8.3) — a self-hosted AI chat platform (fork customized for "Findlay Park AI"). Two-tier architecture: SvelteKit frontend + FastAPI backend, both in a single repo.

### Running services

| Service | Command | Port | Working Dir |
|---------|---------|------|-------------|
| Backend (FastAPI) | `bash backend/dev.sh` | 8080 | `/workspace/backend` |
| Frontend (SvelteKit/Vite) | `npm run dev` | 5173 | `/workspace` |

Both services must run for the full dev experience. The backend uses SQLite by default (zero config, stored at `backend/data/webui.db`).

### Non-obvious caveats

- **npm install requires `--legacy-peer-deps`**: The `@tiptap` packages have peer dependency conflicts between v2 and v3. Always use `npm install --legacy-peer-deps`.
- **`~/.local/bin` must be on PATH**: Python packages install scripts to `~/.local/bin` (e.g., `uvicorn`, `alembic`, `black`). Ensure `export PATH="$HOME/.local/bin:$PATH"` is in your shell profile.
- **Backend startup downloads models**: On first start, the backend downloads the `sentence-transformers/all-MiniLM-L6-v2` model (~90MB) from HuggingFace. This takes ~15-30s. Subsequent starts use the cached model.
- **Backend tests require Docker+PostgreSQL**: All backend pytest tests are integration tests that need Docker with PostgreSQL. They cannot run in environments without Docker.
- **Frontend lint/type-check**: ESLint and `svelte-check` report thousands of pre-existing errors. These are in the existing codebase, not introduced by your changes.
- **CORS for dev**: The backend dev script (`backend/dev.sh`) sets `CORS_ALLOW_ORIGIN` to allow both `:5173` and `:8080`. If starting the backend manually, set this env var.
- **First user is admin**: The first account created on a fresh database is automatically assigned the `admin` role.

### Standard commands reference

See `package.json` scripts section for all available npm commands. Key ones:
- `npm run dev` — start frontend dev server (runs `pyodide:fetch` first)
- `npm run build` — production frontend build
- `npm run lint` — runs ESLint + svelte-check + pylint
- `npm run test:frontend` — vitest (currently no test files)
- `npm run format` — prettier formatting
