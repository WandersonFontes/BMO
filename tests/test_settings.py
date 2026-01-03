import pytest
import os
from src.BMO.config.settings import Settings

def test_settings_load_defaults():
    # Use a fresh instance of Settings to avoid side effects
    settings = Settings()
    assert settings.LOG_LEVEL in ["INFO", "DEBUG", "WARNING", "ERROR"]
    assert hasattr(settings, "LLM_PROVIDER")

def test_full_llm_model_name():
    settings = Settings(LLM_PROVIDER="openai", LLM_MODEL="gpt-4")
    assert settings.FULL_LLM_MODEL_NAME == "gpt-4"

def test_is_configuration_valid():
    # We can't easily test invalid without mocking env, but we can test valid
    settings = Settings(OPENAI_API_KEY="test-key")
    assert settings.is_configuration_valid() is True
