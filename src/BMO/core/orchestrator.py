from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from src.BMO.core.llm import get_llm_client
from src.BMO.skills.registry import registry
# CRITICAL: Import skills to ensure registration
import src.BMO.skills.collection.system_ops

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]

def build_graph():
    """
    Builds the LangGraph agent workflow.
    """
    # 1. Get tools and LLM
    tools = registry.get_tools_list()
    llm = get_llm_client()
    llm_with_tools = llm.bind_tools(tools)

    # 2. Define nodes
    def chatbot(state: AgentState):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    tool_node = ToolNode(tools)

    # 3. Build graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", chatbot)
    workflow.add_node("tools", tool_node)

    workflow.set_entry_point("agent")
    
    # Conditional edge: agent -> tools OR end
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
    )
    
    # Edge: tools -> agent (loop back)
    workflow.add_edge("tools", "agent")

    # 4. Compile with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
