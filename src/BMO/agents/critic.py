from .base import BaseAgent
from .schemas import A2AMessage, AgentResponse, AgentCapabilities
from langchain_core.messages import SystemMessage, HumanMessage

class CriticAgent(BaseAgent):
    """Specialist focused on quality assurance, review, and validation."""
    
    def __init__(self):
        super().__init__(
            name="critic",
            persona="You are a strict Quality Assurance Critic. Your job is to review the outputs of other agents "
                    "against their instructions and constraints. You reject sloppy work, point out missing requirements, "
                    "and approve only high-quality results.",
            tools=[]
        )
        self.capabilities = AgentCapabilities(
            accepts_intents=["review", "validate"],
            produces=["approval", "rejection", "feedback"],
            requires=[]
        )

    async def run(self, message: A2AMessage) -> AgentResponse:
        system_prompt = self._get_system_prompt()
        target_output = message.payload.get("target_output", "")
        criteria = message.constraints or {}
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Review Request from: {message.from_agent}\n"
                                 f"Content to Review: {target_output}\n"
                                 f"Acceptance Criteria: {criteria}\n\n"
                                 f"Evaluate if the content meets the criteria. Return 'APPROVED' or 'REJECTED' with reasons.")
        ]
        
        response = await self.llm.ainvoke(messages)
        content = response.content
        
        # Heuristic to determine status based on LLM output
        final_status = "needs_rework" if "REJECTED" in content else "success"
        
        return AgentResponse(
            status=final_status,
            output={"feedback": content},
            confidence=1.0
        )
