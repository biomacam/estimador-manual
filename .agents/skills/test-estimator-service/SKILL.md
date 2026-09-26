---
name: test-estimator-service
description: 'Use when writing or running pytest tests for the estimator FastAPI service (routers, services, schemas), or mocking LLM provider calls in tests. Triggers: "write a test", "run tests", "pytest", "mock LLM call", "TestClient".'
---

# Test Estimator Service

## When to Use
- Adding test coverage for routers/services in `estimator/`.
- Running the existing test suite.
- Mocking OpenAI/Anthropic calls so tests don't hit real APIs.

## Existing Conventions
- `estimator/tests/conftest.py` exposes a `client` fixture (`fastapi.testclient.TestClient` wrapping `app.main.app`).
- Test files: `tests/test_*.py`, using plain `def test_...(client: TestClient) -> None`.
- `pyproject.toml` sets `asyncio_mode = "auto"` (pytest-asyncio) and `testpaths = ["tests"]`.
- Dev dependencies (`pytest`, `pytest-asyncio`, `httpx`, `ruff`) live in the `dev` dependency group.

## Procedure
1. Run the full suite from the `estimator/` directory:
   ```bash
   uv run pytest
   ```
2. For a new router/service, add `tests/test_<name>.py` using the `client` fixture, following `tests/test_health.py` as the minimal template.
3. To avoid real LLM calls, monkeypatch the service entry point, e.g.:
   ```python
   def test_create_estimation(client, monkeypatch):
       monkeypatch.setattr(
           "app.routers.estimations.generate_estimation",
           lambda transcription: {
               "estimation": "## Fake\n...",
               "model": "gpt-4o-mini",
               "provider": "openai",
               "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
           },
       )
       response = client.post("/api/v1/estimate", json={"transcription": "x" * 60})
       assert response.status_code == 200
   ```
4. To test provider-level failures, monkeypatch `_call_openai`/`_call_anthropic` to raise, and assert the router returns HTTP 500 with the `LLMServiceError` message.
5. Keep assertions on `response.json()` structure aligned with the Pydantic schemas in `app/schemas/`.
