from typing import Any
from .base import BaseAgent
from .schemas import A2AMessage, AgentResponse, AgentCapabilities
from src.BMO.skills.registry import registry
from langchain_core.messages import SystemMessage, HumanMessage
import json

class ResearcherAgent(BaseAgent):
    """Specialist focused on internet search and information gathering."""
    
    def __init__(self):
        # We manually pick tools or search the registry for the specific skill
        search_tool = [t for t in registry.get_tools_list() if t.name == "web_search"]
        super().__init__(
            name="researcher",
            persona="You are a meticulous Research Specialist. You excel at finding precise, current information "
                    "on the web and synthesizing findings into clear summaries with sources.",
            tools=search_tool
        )
        self.capabilities = AgentCapabilities(
            accepts_intents=["research", "fact_check"],
            produces=["summary", "sources"],
            requires=[]
        )

    async def run(self, message: A2AMessage) -> AgentResponse:
        # Bind tools to LLM
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        system_prompt = self._get_system_prompt()
        # Fallback to instruction if query is missing (common with Supervisor)
        query = message.payload.get("query") or message.payload.get("instruction", "")
        
        # Incorporate feedback if retrying
        feedback = message.payload.get("feedback")
        task_content = f"Request from: {message.from_agent}\nIntent: {message.intent}\nTask: {query}"
        
        if feedback:
            task_content += f"\n\n[CRITICAL FEEDBACK FROM PREVIOUS ATTEMPT]: {feedback}"
            
        # Simple interaction loop (can be expanded to a sub-graph later)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=task_content)
        ]
        
        response = await llm_with_tools.ainvoke(messages)
        
        # If the LLM wants to use a tool (web_search)
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # For simplicity in this first version, we execute the tool calls
            tool_results = []
            for tool_call in response.tool_calls:
                tool_to_use = next(t for t in self.tools if t.name == tool_call["name"])
                result = await tool_to_use.ainvoke(tool_call["args"])
                tool_results.append(result)
            
            # Final synthesis after tool use
            messages.append(response)
            messages.append(HumanMessage(content=f"Tool results: {tool_results}\n\nPlease synthesize the final answer."))
            final_res = await self.llm.ainvoke(messages)
            content = final_res.content
        else:
            content = response.content

        return AgentResponse(
            status="success",
            output={"content": content, "summary": content},
            confidence=1.0
        )
