from fastapi.testclient import TestClient

from app.context.examples import ESTIMATION_EXAMPLES
from app.services.llm_service import LLMServiceError, build_system_prompt


def test_examples_reach_the_system_prompt() -> None:
    prompt = build_system_prompt()

    for example in ESTIMATION_EXAMPLES:
        assert example["estimation"] in prompt


def test_provider_error_does_not_leak_details(client: TestClient, monkeypatch) -> None:
    def boom(*args, **kwargs):
        raise LLMServiceError("sk-proj-super-secret-key-fragment")

    monkeypatch.setattr("app.routers.estimations.generate_estimation", boom)

    response = client.post("/api/v1/estimate", json={"transcription": "x" * 60})

    assert response.status_code == 500
    assert "sk-proj" not in response.text
