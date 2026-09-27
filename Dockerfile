# ---- Builder: install dependencies with uv ----
FROM python:3.11-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project --no-dev --locked

COPY . .

# ---- Runtime: slim image, non-root user ----
FROM python:3.11-slim AS runtime

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

# No curl in the slim image: use urllib to hit the FastAPI health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
