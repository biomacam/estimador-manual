import structlog

from app.config import get_settings
from app.context.examples import ESTIMATION_EXAMPLES, format_examples_for_prompt

log = structlog.get_logger()

MAX_TOKENS = 4000


class LLMServiceError(Exception):
    """Raised when the LLM provider call fails."""


def build_system_prompt() -> str:
    """Build the system prompt: estimator role + injected CAG reference examples."""
    examples_block = format_examples_for_prompt(ESTIMATION_EXAMPLES)
    return (
        "You are an expert software estimator with 15 years of experience scoping "
        "and pricing software projects. Given the transcription of a client "
        "meeting, you produce a detailed, realistic project estimation.\n\n"
        "Use the following past estimations as reference for format, level of "
        "detail, and pricing (62.50 EUR/hour developer rate, 50 EUR/hour "
        "designer rate). Your answer MUST follow the same markdown structure:\n "
        "- A project title as an H2 heading \n"
        "- A 'Task Breakdown' table with columns Task | Hours | Cost (EUR) \n"
        "- A 'Totals' section with cost in EUR\n"
        "- A 'Total hours' section \n"
        "- A 'Recommended Team' section\n"
        "- An 'Estimated Duration' section in weeks.\n\n"
        " Provide realistic, well-justified numbers.\n\n"
        f"{examples_block}"
    )


def _call_openai(system_prompt: str, transcription: str, model: str) -> dict:
    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcription},
        ],
        max_tokens=MAX_TOKENS,
    )
    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0
    log.info(
        "llm_response_received",
        provider="openai",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    return {
        "estimation": response.choices[0].message.content,
        "model": model,
        "provider": "openai",
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        },
    }


def _call_anthropic(system_prompt: str, transcription: str, model: str) -> dict:
    from anthropic import Anthropic

    settings = get_settings()
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": transcription}],
    )
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    log.info(
        "llm_response_received",
        provider="anthropic",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    estimation_text = "".join(
        block.text for block in response.content if block.type == "text"
    )
    return {
        "estimation": estimation_text,
        "model": model,
        "provider": "anthropic",
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        },
    }


def generate_estimation(transcription: str) -> dict:
    """Generate a project estimation from a meeting transcription using the configured LLM provider."""
    settings = get_settings()
    system_prompt = build_system_prompt()

    try:
        if settings.LLM_PROVIDER == "openai":
            return _call_openai(system_prompt, transcription, settings.LLM_MODEL)
        elif settings.LLM_PROVIDER == "anthropic":
            return _call_anthropic(system_prompt, transcription, settings.LLM_MODEL)
        raise LLMServiceError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
    except LLMServiceError:
        raise
    except Exception as exc:
        raise LLMServiceError(f"LLM call failed: {exc}") from exc
