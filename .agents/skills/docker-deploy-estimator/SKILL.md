---
name: docker-deploy-estimator
description: 'Use when building, running, or troubleshooting the estimator service via Docker/Docker Compose, editing the Dockerfile, or configuring environment variables for local/production runs. Triggers: "docker compose", "Dockerfile", "container", "deploy", "env vars".'
---

# Docker Deploy (estimator)

## When to Use
- Running the service locally via Docker Compose.
- Modifying the multi-stage `Dockerfile` or `docker-compose.yml`.
- Debugging container healthcheck or env var issues.

## Existing Setup
- `Dockerfile`: two-stage build (`builder` installs deps with `uv sync --no-install-project --no-dev`; `runtime` is a slim `python:3.11-slim` image running as non-root `appuser`). Healthcheck hits `/health` via `urllib.request` (no curl in slim image). `CMD` runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- `docker-compose.yml`: builds the local image, maps port `8000:8000`, loads `.env` via `env_file`, bind-mounts `./app:/app/app` for hot reload, and overrides `command` to add `--reload`. Remove the volume mount and `--reload` for production.

## Procedure
1. Local run:
   ```bash
   cd estimator
   cp .env.example .env   # set OPENAI_API_KEY / ANTHROPIC_API_KEY and LLM_PROVIDER
   docker compose up --build
   ```
   Service available at `http://localhost:8000` (docs at `/docs`).
2. Required env vars come from `app/config.py`'s `Settings`: `LLM_PROVIDER` (`openai`|`anthropic`), matching `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`, `LLM_MODEL`, `APP_ENV`, `LOG_LEVEL`. Missing the key for the selected provider fails fast at startup (`validate_api_key_for_provider`).
3. For production images: drop the `volumes` bind mount and the `--reload` flag override in `docker-compose.yml` (or use a separate `docker-compose.prod.yml`), keep the image's default `CMD`.
4. To add a new runtime dependency, add it to `pyproject.toml` `dependencies` — the builder stage re-runs `uv sync` only when `pyproject.toml`/`uv.lock` change (Docker layer caching).
5. Troubleshoot healthcheck failures with `docker compose logs estimator` and confirm `/health` returns `{"status": "healthy"}` (see `app/main.py`).
