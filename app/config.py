from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_MODELS: dict[str, str] = {
	"openai": "gpt-4o-mini",
	"anthropic": "claude-haiku-4-5",
}


class Settings(BaseSettings):
	OPENAI_API_KEY: str | None = None
	ANTHROPIC_API_KEY: str | None = None
	LLM_PROVIDER: Literal["openai", "anthropic"] = "openai"
	LLM_MODEL: str | None = None
	LLM_TIMEOUT_SECONDS: float = 30.0
	LLM_MAX_RETRIES: int = 2
	APP_ENV: str = "development"
	LOG_LEVEL: str = "DEBUG"

	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="ignore",
	)

	@model_validator(mode="after")
	def resolve_model_for_provider(self) -> "Settings":
		if not self.LLM_MODEL:
			self.LLM_MODEL = DEFAULT_MODELS[self.LLM_PROVIDER]
		return self

	@model_validator(mode="after")
	def validate_api_key_for_provider(self) -> "Settings":
		api_key = (
			self.OPENAI_API_KEY
			if self.LLM_PROVIDER == "openai"
			else self.ANTHROPIC_API_KEY
		)
		if not api_key:
			raise ValueError(
				f"{self.LLM_PROVIDER.upper()}_API_KEY is required "
				f"when LLM_PROVIDER is '{self.LLM_PROVIDER}'"
			)
		return self


@lru_cache
def get_settings() -> Settings:
	return Settings()
