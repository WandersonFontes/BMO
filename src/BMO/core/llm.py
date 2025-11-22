from langchain_community.chat_models import ChatLiteLLM
from src.BMO.config.settings import settings

def get_llm_client() -> ChatLiteLLM:
    """
    Returns a configured ChatLiteLLM instance.
    """
    return ChatLiteLLM(
        model=settings.FULL_LLM_MODEL_NAME,
        streaming=True,
        temperature=0
    )
