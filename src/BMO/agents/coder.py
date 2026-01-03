from .base import BaseAgent
from .schemas import A2AMessage, AgentResponse, AgentCapabilities
from src.BMO.skills.registry import registry
from langchain_core.messages import SystemMessage, HumanMessage

class CoderAgent(BaseAgent):
    """Specialist focused on system operations and code generation."""
    
    def __init__(self):
        # Tools for system operations and file management
        coder_tools = [t for t in registry.get_tools_list() if t.name in ["get_system_info", "system_manager_files"]]
        super().__init__(
            name="coder",
            persona="You are a Senior Software Engineer and System Administrator. You specialize in "
                    "operating system interaction, file management, and writing clean, executable code.",
            tools=coder_tools
        )
        self.capabilities = AgentCapabilities(
            accepts_intents=["code_generation", "refactor"],
            produces=["code", "files"],
            requires=[]
        )

    async def run(self, message: A2AMessage) -> AgentResponse:
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        system_prompt = self._get_system_prompt()
        instruction = message.payload.get("instruction", "")
        feedback = message.payload.get("feedback")
        
        task_content = f"Request from: {message.from_agent}\nIntent: {message.intent}\nTask: {instruction}"
        
        if feedback:
             task_content += f"\n\n[CRITICAL FEEDBACK FROM PREVIOUS ATTEMPT]: {feedback}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=task_content)
        ]
        
        response = await llm_with_tools.ainvoke(messages)
        
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # We execute the tool calls
            for tool_call in response.tool_calls:
                tool_to_use = next(t for t in self.tools if t.name == tool_call["name"])
                result = await tool_to_use.ainvoke(tool_call["args"])
                messages.append(response)
                messages.append(HumanMessage(content=f"Tool '{tool_call['name']}' result: {result}"))
            
            final_res = await self.llm.ainvoke(messages)
            content = final_res.content
        else:
            content = response.content

        return AgentResponse(
            status="success",
            output={"content": content, "code": content},
            confidence=1.0
        )
