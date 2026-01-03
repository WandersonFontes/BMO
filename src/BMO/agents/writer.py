from .base import BaseAgent
from .schemas import A2AMessage, AgentResponse, AgentCapabilities
from langchain_core.messages import SystemMessage, HumanMessage

class WriterAgent(BaseAgent):
    """Specialist focused on synthesis, creative writing, and documentation."""
    
    def __init__(self):
        super().__init__(
            name="writer",
            persona="You are a versatile AI Assistant and Technical Writer. You excel at both clear, structured "
                    "documentation and friendly, concise conversational replies. Adapt your tone to the task.",
            tools=[] # Writers usually don't need tools, they use the context provided
        )
        self.capabilities = AgentCapabilities(
            accepts_intents=["write", "summarize", "format"],
            produces=["draft", "document"],
            requires=[]
        )

    async def run(self, message: A2AMessage) -> AgentResponse:
        system_prompt = self._get_system_prompt()
        # 'context' attr does not exist in A2AMessage, using payload for background_info
        context_data = message.payload.get("background_info", "No background provided.")
        instruction = message.payload.get("instruction", "")
        feedback = message.payload.get("feedback")
        
        task_content = f"Context from: {message.from_agent}\nBackground: {context_data}\n\nTask: {instruction}"
        
        if feedback:
             task_content += f"\n\n[CRITICAL FEEDBACK FROM PREVIOUS ATTEMPT]: {feedback}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=task_content)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        return AgentResponse(
            status="success",
            output={"content": response.content, "document": response.content},
            confidence=1.0
        )
