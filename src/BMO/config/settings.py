from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o"
    OPENAI_API_KEY: str | None = None
    DATABASE_URL: str | None = None

    @computed_field
    @property
    def FULL_LLM_MODEL_NAME(self) -> str:
        if self.LLM_PROVIDER == "ollama":
            return f"ollama/{self.LLM_MODEL}"
        return self.LLM_MODEL

settings = Settings()
