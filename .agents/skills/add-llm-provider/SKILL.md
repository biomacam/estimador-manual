---
name: add-llm-provider
description: 'Use when adding support for a new LLM provider (e.g. Gemini, Mistral, Azure OpenAI) to the estimator service, or when modifying how LLM_PROVIDER is selected/validated. Triggers: "add provider", "new LLM", "support Gemini/Mistral", "switch LLM provider".'
---

# Add LLM Provider (estimator)

## When to Use
- Adding a new LLM provider alongside the existing OpenAI/Anthropic support.
- Changing the provider selection or API-key validation logic.

## Existing Pattern
- `estimator/app/config.py`: `Settings.LLM_PROVIDER` is a `Literal["openai", "anthropic"]`; `validate_api_key_for_provider` (a `model_validator`) enforces that the matching `*_API_KEY` is set.
- `estimator/app/services/llm_service.py`: `generate_estimation()` dispatches on `settings.LLM_PROVIDER` to a private `_call_<provider>()` function. Each function lazily imports its SDK inside the function body (keeps optional deps out of module import time) and returns a dict shaped like:
  ```python
  {
      "estimation": str,
      "model": str,
      "provider": str,
      "usage": {"input_tokens": int, "output_tokens": int, "total_tokens": int},
  }
  ```
- Provider-agnostic failures are wrapped as `LLMServiceError` and surfaced by the router as HTTP 500.

## Procedure
1. In `app/config.py`: extend the `LLM_PROVIDER` `Literal` with the new value, add the corresponding `<PROVIDER>_API_KEY: str | None = None` field, and add a branch in `validate_api_key_for_provider`.
2. Add the provider's SDK to `dependencies` in `pyproject.toml`.
3. In `app/services/llm_service.py`, add a `_call_<provider>(...)` function mirroring `_call_openai`/`_call_anthropic`: build the request, call `structlog` `log.info("llm_response_received", provider=..., input_tokens=..., output_tokens=...)`, and return the same dict shape.
4. Add a branch for the new provider in `generate_estimation()`'s if/elif dispatch (keep the existing `try/except` wrapping into `LLMServiceError`).
5. Document the new env var in `estimator/README.md` and `.env.example`.
6. Add/update a test that monkeypatches the new `_call_<provider>` to avoid real API calls (see the `test-estimator-service` skill).
