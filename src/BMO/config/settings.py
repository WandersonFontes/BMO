import os
import logging
from typing import Optional, List, Dict, Any
from pydantic import computed_field, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure logger
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings configuration for BMO Assistant.
    
    This class handles all configuration management including environment variables,
    .env file loading, validation, and computed properties. It follows the 12-factor
    app methodology for configuration.
    
    Attributes:
        LLM_PROVIDER: The LLM provider to use (openai, anthropic, ollama, etc.)
        LLM_MODEL: The specific model identifier for the chosen provider
        OPENAI_API_KEY: API key for OpenAI services (optional for some providers)
        ANTHROPIC_API_KEY: API key for Anthropic services
        OLLAMA_BASE_URL: Base URL for Ollama API (defaults to localhost)
        DATABASE_URL: Database connection string
        SYSTEM_PROMPT: The system prompt that defines BMO's personality and behavior
        LOG_LEVEL: Application logging level
        MAX_MEMORY_MESSAGES: Maximum number of messages to keep in memory
        REQUEST_TIMEOUT: Timeout for API requests in seconds
        
    Example:
        >>> from src.BMO.config.settings import settings
        >>> print(f"Using model: {settings.FULL_LLM_MODEL_NAME}")
        Using model: gpt-4o
    """
    
    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        validate_default=True
    )

    # LLM Configuration
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Application Configuration
    DATABASE_PATH: str = "persistence/bmo_history.sqlite"
    DATABASE_URL: Optional[str] = None
    SYSTEM_PROMPT: str = (
        "You are BMO, a helpful and modular AI Assistant. "
        "You are friendly, knowledgeable, and always strive to provide "
        "accurate and useful responses. You can use various tools to "
        "help users with their tasks."
    )
    
    # Runtime Configuration
    LOG_LEVEL: str = "INFO"
    MAX_MEMORY_MESSAGES: int = 50
    REQUEST_TIMEOUT: int = 60
    ENABLE_STREAMING: bool = True
    
    # Security Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    ENABLE_AUTH: bool = False
    
    # Feature Flags
    ENABLE_WEB_SEARCH: bool = True
    ENABLE_FILE_OPS: bool = True
    ENABLE_SYSTEM_OPS: bool = False  # Disabled by default for security

    @computed_field
    @property
    def FULL_LLM_MODEL_NAME(self) -> str:
        """
        Compute the full model name based on provider and model.
        
        Returns:
            Formatted model name appropriate for the chosen provider.
            Examples:
            - OpenAI: "gpt-4o"
            - Ollama: "ollama/llama2"
            - Anthropic: "claude-3-sonnet-20240229"
        """
        provider_model_map: Dict[str, str] = {
            "openai": self.LLM_MODEL,
            "ollama": f"ollama/{self.LLM_MODEL}",
            "anthropic": self.LLM_MODEL,
            "azure_openai": f"azure/{self.LLM_MODEL}",
        }
        
        full_name: str = provider_model_map.get(
            self.LLM_PROVIDER.lower(), 
            self.LLM_MODEL
        )
        logger.debug(f"Computed full model name: {full_name}")
        return full_name

    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate that the LLM provider is supported."""
        supported_providers: List[str] = ["openai", "anthropic", "ollama", "azure_openai"]
        if v.lower() not in supported_providers:
            raise ValueError(
                f"Unsupported LLM provider: {v}. "
                f"Supported providers: {', '.join(supported_providers)}"
            )
        return v.lower()

    @field_validator("OPENAI_API_KEY", "ANTHROPIC_API_KEY")
    @classmethod
    def validate_api_keys(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate API keys when required by the provider."""
        if not v and info.field_name == "OPENAI_API_KEY" and info.data.get("LLM_PROVIDER") == "openai":
            logger.warning("OPENAI_API_KEY is not set but OpenAI provider is selected")
        elif not v and info.field_name == "ANTHROPIC_API_KEY" and info.data.get("LLM_PROVIDER") == "anthropic":
            logger.warning("ANTHROPIC_API_KEY is not set but Anthropic provider is selected")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate and normalize log level."""
        valid_levels: List[str] = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Valid levels: {', '.join(valid_levels)}")
        return v.upper()

    @field_validator("MAX_MEMORY_MESSAGES")
    @classmethod
    def validate_memory_messages(cls, v: int) -> int:
        """Validate memory messages limit."""
        if v < 1:
            raise ValueError("MAX_MEMORY_MESSAGES must be at least 1")
        if v > 1000:
            logger.warning("MAX_MEMORY_MESSAGES is set very high, may impact performance")
        return v

    @field_validator("REQUEST_TIMEOUT")
    @classmethod
    def validate_request_timeout(cls, v: int) -> int:
        """Validate request timeout value."""
        if v < 1:
            raise ValueError("REQUEST_TIMEOUT must be at least 1 second")
        if v > 300:
            logger.warning("REQUEST_TIMEOUT is set very high, may cause long waits")
        return v

    @computed_field
    @property
    def IS_DEBUG_MODE(self) -> bool:
        """Check if application is in debug mode."""
        return self.LOG_LEVEL == "DEBUG"

    @computed_field
    @property
    def IS_LOCAL_MODEL(self) -> bool:
        """Check if using a local model (Ollama)."""
        return self.LLM_PROVIDER.lower() == "ollama"

    @computed_field
    @property
    def REQUIRED_API_KEYS(self) -> Dict[str, Optional[str]]:
        """Get required API keys for the current configuration."""
        required_keys: Dict[str, Optional[str]] = {}
        if self.LLM_PROVIDER == "openai":
            required_keys["OPENAI_API_KEY"] = self.OPENAI_API_KEY
        elif self.LLM_PROVIDER == "anthropic":
            required_keys["ANTHROPIC_API_KEY"] = self.ANTHROPIC_API_KEY
        return required_keys

    @property
    def EFFECTIVE_DATABASE_URL(self) -> str:
        """Get the effective database URL or path."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return self.DATABASE_PATH

    def ensure_database_dir(self) -> None:
        """Ensure the directory for the database exists."""
        db_dir = os.path.dirname(self.DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Created database directory: {db_dir}")
            except OSError as e:
                logger.error(f"Failed to create database directory {db_dir}: {e}")

    def is_configuration_valid(self) -> bool:
        """
        Validate if the current configuration is sufficient for operation.
        
        Returns:
            True if configuration is valid, False otherwise.
        """
        try:
            # Check required API keys
            if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
                logger.error("OpenAI provider selected but OPENAI_API_KEY is not set")
                return False
            elif self.LLM_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
                logger.error("Anthropic provider selected but ANTHROPIC_API_KEY is not set")
                return False
            
            # Check for local Ollama if provider is ollama
            if self.LLM_PROVIDER == "ollama":
                logger.info("Using local Ollama provider, ensure Ollama is running")
            
            logger.info(f"Configuration validated successfully for provider: {self.LLM_PROVIDER}")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def get_safe_config(self) -> Dict[str, Any]:
        """
        Get configuration with sensitive values masked for logging.
        
        Returns:
            Dictionary with sensitive values masked.
        """
        config: Dict[str, Any] = self.model_dump()
        sensitive_fields: List[str] = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DATABASE_URL"]
        
        for field in sensitive_fields:
            if field in config and config[field]:
                config[field] = "***MASKED***"
                
        return config

    def __str__(self) -> str:
        """String representation of settings."""
        return f"Settings(provider={self.LLM_PROVIDER}, model={self.LLM_MODEL})"

    def __repr__(self) -> str:
        """Detailed representation of settings."""
        return (f"Settings(LLM_PROVIDER='{self.LLM_PROVIDER}', "
                f"LLM_MODEL='{self.LLM_MODEL}', "
                f"LOG_LEVEL='{self.LOG_LEVEL}')")

# Global settings instance
settings = Settings()

# Validate configuration on startup
if settings.is_configuration_valid():
    logger.info(
        f"BMO Settings initialized: {settings.LLM_PROVIDER}/{settings.LLM_MODEL}",
        extra={"config": settings.get_safe_config()}
    )
else:
    logger.warning(
        "BMO Settings initialized with configuration issues",
        extra={"config": settings.get_safe_config()}
    )


def reload_settings() -> Settings:
    """
    Reload settings from environment and .env file.
    
    Useful for development when .env files change or for testing.
    
    Returns:
        Reloaded settings instance.
    """
    global settings
    settings = Settings()
    
    # Re-validate after reload
    settings.is_configuration_valid()
    logger.info("Settings reloaded from environment")
    
    return settings