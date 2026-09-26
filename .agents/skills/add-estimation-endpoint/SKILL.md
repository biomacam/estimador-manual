---
name: add-estimation-endpoint
description: 'Use when adding a new API endpoint or router to the estimator FastAPI service, following its layered architecture (router -> schema -> service -> context/config). Triggers: "add endpoint", "new route", "new router", "expose API".'
---

# Add Estimation Endpoint (layered architecture)

## When to Use
- Adding a new HTTP endpoint to the estimator service beyond `/api/v1/estimate` and `/health`.

## Existing Layering (must be respected)
1. **Router** (`app/routers/`) — FastAPI `APIRouter`, request/response only via schemas, translates domain exceptions to `HTTPException`. No business logic.
2. **Schema** (`app/schemas/`) — Pydantic `BaseModel`s defining the request/response contract (`Field(..., description=...)`), validated at the boundary.
3. **Service** (`app/services/`) — business logic, orchestrates calls to `context/` and `config`, raises a dedicated `<X>ServiceError` exception on failure.
4. **Context/Config** (`app/context/`, `app/config.py`) — static knowledge base and environment-driven settings (`get_settings()`, `lru_cache`d singleton).

## Procedure
1. Define request/response models in `app/schemas/<name>.py` (mirror `EstimationRequest`/`EstimationResponse` in `estimator/app/schemas/estimation.py`).
2. Implement the logic in `app/services/<name>_service.py`: define a module-level `<Name>ServiceError(Exception)`, use `structlog.get_logger()` for `log.info`/`log.error`, and read settings via `get_settings()` — never read env vars directly.
3. Create `app/routers/<name>.py` with `router = APIRouter(prefix="/api/v1", tags=["<name>"])`, a handler that calls the service and catches its `ServiceError` to raise `HTTPException(status_code=500, detail=str(exc))`.
4. Register the router in `estimator/app/main.py` via `app.include_router(<name>.router)`.
5. Add tests under `estimator/tests/` following the `client` fixture in `conftest.py`.
6. Update the architecture diagram/table in `estimator/README.md` if a new layer or external dependency is introduced.

## FastAPI convention: `async def` vs `def` in route handlers
`async def` only helps when the body actually `await`s non-blocking I/O. The current `create_estimation` handler in `app/routers/estimations.py` is declared `async def` but calls the fully synchronous `generate_estimation()` (blocking OpenAI/Anthropic SDK calls, no `await`) — this runs the blocking call directly on the event loop instead of FastAPI's threadpool, which can stall other concurrent requests.
- If the service call chain stays synchronous/blocking, declare the handler as plain `def` — FastAPI will run it in an external threadpool automatically.
- Only use `async def` once the underlying service is truly async (e.g. using `AsyncOpenAI`/`AsyncAnthropic` with real `await` calls).
