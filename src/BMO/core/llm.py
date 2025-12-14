import logging
from typing import Optional, Dict, Any, Set
from langchain_litellm import ChatLiteLLM
from src.BMO.config.settings import settings

logger = logging.getLogger(__name__)

def get_llm_client(
    model: Optional[str] = None,
    streaming: Optional[bool] = None,
    temperature: Optional[float] = None,
    **additional_kwargs: Any
) -> ChatLiteLLM:
    """
    Factory function to create a configured ChatLiteLLM instance.
    
    This function creates a LiteLLM chat client with sensible defaults that can be
    overridden by parameters or environment settings. It includes validation and
    error handling for robust client creation.
    
    Args:
        model: The LLM model to use. If None, uses settings.FULL_LLM_MODEL_NAME.
        streaming: Whether to enable streaming responses. Defaults to True.
        temperature: Controls randomness in output (0.0 = deterministic, 1.0 = creative).
                    Defaults to 0.0 for consistent results.
        **additional_kwargs: Additional parameters to pass to ChatLiteLLM constructor.
        
    Returns:
        Configured ChatLiteLLM instance ready for use.
        
    Raises:
        ValueError: If required model name is missing or invalid.
        RuntimeError: If LLM client cannot be initialized due to configuration issues.
        
    Example:
        >>> # Basic usage with default settings
        >>> llm = get_llm_client()
        
        >>> # Custom configuration
        >>> llm = get_llm_client(
        ...     model="gpt-4",
        ...     temperature=0.3,
        ...     max_tokens=1000
        ... )
        
        >>> # For testing with more creative responses
        >>> llm = get_llm_client(temperature=0.7, streaming=False)
    """
    # Resolve configuration with fallbacks
    final_model: str = model or getattr(settings, 'FULL_LLM_MODEL_NAME', None)
    if not final_model:
        error_msg: str = (
            "LLM model name not provided and FULL_LLM_MODEL_NAME setting is not configured. "
            "Please provide a model name or configure the FULL_LLM_MODEL_NAME setting."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    final_streaming: bool = streaming if streaming is not None else True
    final_temperature: float = temperature if temperature is not None else 0.0
    
    # Validate parameters
    _validate_llm_parameters(
        model=final_model,
        temperature=final_temperature,
        streaming=final_streaming
    )
    
    # Prepare base configuration
    llm_config: Dict[str, Any] = {
        "model": final_model,
        "streaming": final_streaming,
        "temperature": final_temperature,
    }

    # Inject API key if available
    api_key: Optional[str] = None
    if settings.LLM_PROVIDER == "openai":
        api_key = settings.OPENAI_API_KEY
    elif settings.LLM_PROVIDER == "anthropic":
        api_key = settings.ANTHROPIC_API_KEY
    
    if api_key:
        llm_config["api_key"] = api_key
    
    # Add any additional kwargs
    llm_config.update(additional_kwargs)
    
    try:
        logger.info(
            f"Initializing ChatLiteLLM with model: {final_model}, "
            f"streaming: {final_streaming}, temperature: {final_temperature}"
        )
        
        client: ChatLiteLLM = ChatLiteLLM(**llm_config)
        
        logger.debug(f"Successfully created ChatLiteLLM client with config: {_mask_sensitive_config(llm_config)}")
        return client
        
    except Exception as e:
        error_msg: str = f"Failed to initialize ChatLiteLLM client: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e

def _validate_llm_parameters(
    model: str,
    temperature: float,
    streaming: bool
) -> None:
    """
    Validate LLM configuration parameters.
    
    Args:
        model: Model name to validate.
        temperature: Temperature value to validate (0.0-2.0).
        streaming: Streaming flag to validate.
        
    Raises:
        ValueError: If any parameter is invalid.
    """
    if not model or not isinstance(model, str):
        raise ValueError(f"Invalid model name: {model}. Must be a non-empty string.")
    
    if not isinstance(temperature, (int, float)) or not 0.0 <= temperature <= 2.0:
        raise ValueError(f"Invalid temperature: {temperature}. Must be a float between 0.0 and 2.0.")
    
    if not isinstance(streaming, bool):
        raise ValueError(f"Invalid streaming value: {streaming}. Must be a boolean.")

def _mask_sensitive_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask sensitive configuration values for logging.
    
    Args:
        config: Original configuration dictionary.
        
    Returns:
        Configuration dictionary with sensitive values masked.
    """
    sensitive_keys: Set[str] = {'api_key', 'key', 'password', 'secret', 'token'}
    masked_config: Dict[str, Any] = config.copy()
    
    for key in masked_config:
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            masked_config[key] = '***MASKED***'
    
    return masked_config

def get_test_llm_client() -> ChatLiteLLM:
    """
    Create a test LLM client with conservative settings.
    
    Useful for testing and development with consistent, deterministic behavior.
    
    Returns:
        ChatLiteLLM client configured for testing.
    """
    return get_llm_client(
        streaming=False,
        temperature=0.0,
        request_timeout=30
    )

def get_creative_llm_client(temperature: float = 0.7) -> ChatLiteLLM:
    """
    Create an LLM client configured for creative tasks.
    
    Args:
        temperature: Controls creativity (0.1-1.0). Higher values more creative.
        
    Returns:
        ChatLiteLLM client configured for creative generation.
    """
    if not 0.1 <= temperature <= 1.0:
        logger.warning(f"Creative temperature {temperature} outside recommended range 0.1-1.0")
    
    return get_llm_client(
        temperature=temperature,
        streaming=True
    )

# Convenience instance for common use cases
_default_llm_client: Optional[ChatLiteLLM] = None

def get_default_llm_client() -> ChatLiteLLM:
    """
    Get or create a singleton default LLM client.
    
    Returns cached client instance to avoid repeated initialization
    when the same configuration is needed multiple times.
    
    Returns:
        Cached default ChatLiteLLM instance.
    """
    global _default_llm_client
    
    if _default_llm_client is None:
        _default_llm_client = get_llm_client()
    
    return _default_llm_client