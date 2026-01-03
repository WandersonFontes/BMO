from abc import ABC, abstractmethod
from typing import List, Optional
from langchain_core.tools import BaseTool
from .schemas import A2AMessage, AgentResponse, AgentCapabilities
from src.BMO.core.llm import get_llm_client
from src.BMO.config.settings import settings

class BaseAgent(ABC):
    """Base class for BMO specialists acting as 'Pure Executors'."""
    
    capabilities: AgentCapabilities

    def __init__(self, name: str, persona: str, tools: Optional[List[BaseTool]] = None):
        self.name = name
        self.persona = persona
        self.tools = tools or []
        # Agents still need an LLM for their specific cognitive tasks (e.g. summarizing, extracting)
        self.llm = get_llm_client(
            streaming=True
        )

    @abstractmethod
    async def run(self, message: A2AMessage) -> AgentResponse:
        """Execute the agent logic based on the received A2A message."""
        pass

    def _get_system_prompt(self) -> str:
        """Construct the specialist's system prompt."""
        return f"PERSONA: {self.persona}\n\nYou are a specialized agent in the BMO (Modular AI Assistant) ecosystem. " \
               "Your goal is to fulfill the 'intent' provided in the A2A message using your tools and expertise. " \
               "Always be concise and return structured, high-quality results."
