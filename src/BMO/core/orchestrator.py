import logging
from typing import TypedDict, Annotated, Sequence, Dict, Any, Optional, List, Callable
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langchain_litellm import ChatLiteLLM
from langchain_core.tools import BaseTool

from src.BMO.core.llm import get_llm_client
from src.BMO.config.settings import settings
from src.BMO.skills.registry import registry

# Configure logger
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """
    State definition for the BMO agent workflow.
    
    Attributes:
        messages: Sequence of messages in the conversation, automatically updated
                 with new messages using the add_messages annotation.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]

def _import_skill_modules() -> None:
    """
    Import all skill modules to ensure they are registered with the registry.
    
    Uses the registry's auto-discovery mechanism to find plugins in the
    collection directory.
    """
    try:
        # Dynamic discovery of skills
        # We import inside function to avoid circular imports if any
        from src.BMO.skills.registry import registry
        count = registry.discover_skills("src.BMO.skills.collection")
        logger.info(f"Discovered and potentially registered skills from {count} modules")
        
    except Exception as e:
        logger.error(f"Failed to discover skills: {e}")
        raise RuntimeError("Skill discovery failed") from e

def _create_llm_with_tools() -> Any:
    """
    Create and configure LLM client with registered tools.
    
    Returns:
        LLM client bound with all available tools from the registry.
        
    Raises:
        RuntimeError: If no tools are registered or LLM client cannot be configured.
    """
    try:
        tools: List[BaseTool] = registry.get_tools_list()
        if not tools:
            raise RuntimeError("No tools available in registry. Skill registration may have failed.")
        
        logger.info(f"Loaded {len(tools)} tools: {[tool.name for tool in tools]}")
        
        llm: ChatLiteLLM = get_llm_client()
        llm_with_tools: ChatLiteLLM = llm.bind_tools(tools)
        
        return llm_with_tools
        
    except Exception as e:
        logger.error(f"Failed to create LLM with tools: {e}")
        raise RuntimeError(f"LLM tool binding failed: {e}") from e

def _create_agent_node(llm_with_tools: ChatLiteLLM) -> Callable[[AgentState], Dict[str, Any]]:
    """
    Create the agent node that handles reasoning and decision making.
    
    Args:
        llm_with_tools: LLM client configured with available tools.
        
    Returns:
        Function that represents the agent node in the graph.
    """
    def chatbot(state: AgentState) -> Dict[str, Any]:
        """
        Agent node that processes messages and decides on tool usage.
        
        Args:
            state: Current agent state containing message history.
            
        Returns:
            Updated state with agent's response message.
            
        Raises:
            Exception: Propagates any exceptions from LLM invocation.
        """
        try:
            # Prepend system prompt to conversation context
            system_message: SystemMessage = SystemMessage(content=settings.SYSTEM_PROMPT)
            messages: List[BaseMessage] = [system_message] + list(state["messages"])
            
            logger.debug(f"Agent processing {len(messages)} messages")
            response: BaseMessage = llm_with_tools.invoke(messages)
            
            logger.info("Agent node completed processing")
            return {"messages": [response]}
            
        except Exception as e:
            logger.error(f"Agent node execution failed: {e}")
            # Return a helpful error message to the user
            error_message: SystemMessage = SystemMessage(
                content="I apologize, but I encountered an error while processing your request. Please try again."
            )
            return {"messages": [error_message]}
    
    return chatbot

def _build_workflow_structure(llm_with_tools: ChatLiteLLM) -> StateGraph[AgentState]:
    """
    Build the complete workflow graph with all nodes and edges.
    
    Args:
        llm_with_tools: Configured LLM client for the agent node.
        
    Returns:
        Compiled StateGraph ready for execution.
    """
    # Create graph with state definition
    workflow: StateGraph[AgentState] = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", _create_agent_node(llm_with_tools))
    workflow.add_node("tools", ToolNode(registry.get_tools_list()))
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Define conditional routing: agent -> tools OR end
    workflow.add_conditional_edges(
        "agent",
        tools_condition,  # Decides whether to use tools or end conversation
        {
            "tools": "tools",  # If tools needed, go to tools node
            END: END           # If no tools needed, end conversation
        }
    )
    
    # Define loop back: tools -> agent (continue processing)
    workflow.add_edge("tools", "agent")
    
    logger.debug("Workflow structure built successfully")
    return workflow

def build_graph() -> StateGraph[AgentState]:
    """
    Build and compile the LangGraph agent workflow.
    
    This function constructs the complete agent graph with:
    - Tool-registered LLM for reasoning
    - Tool execution capabilities  
    - Conditional routing between reasoning and tool use
    - Persistent memory for multi-turn conversations
    
    Returns:
        Compiled LangGraph agent ready for interaction.
        
    Raises:
        RuntimeError: If graph construction fails due to configuration issues,
                     missing tools, or LLM connectivity problems.
                     
    Example:
        >>> graph = build_graph()
        >>> config = {"configurable": {"thread_id": "user123"}}
        >>> result = graph.invoke({"messages": [HumanMessage(content="Hello")]}, config)
    """
    logger.info("Starting LangGraph workflow construction")
    
    try:
        # Ensure all skills are registered
        _import_skill_modules()
        
        # Configure LLM with available tools
        llm_with_tools: ChatLiteLLM = _create_llm_with_tools()
        
        # Build graph structure
        workflow: StateGraph[AgentState] = _build_workflow_structure(llm_with_tools)
        
        # Compile with memory persistence
        memory: MemorySaver = MemorySaver()
        compiled_graph = workflow.compile(checkpointer=memory)
        
        logger.info("LangGraph workflow compiled successfully")
        return compiled_graph
        
    except Exception as e:
        logger.error(f"Failed to build LangGraph workflow: {e}")
        raise RuntimeError(f"Workflow construction failed: {e}") from e

def get_graph_config(thread_id: str) -> Dict[str, Any]:
    """
    Create configuration for graph execution with thread-specific memory.
    
    Args:
        thread_id: Unique identifier for conversation thread.
        
    Returns:
        Configuration dictionary for graph invocation.
    """
    return {
        "configurable": {
            "thread_id": thread_id
        }
    }

# Pre-compiled graph instance for singleton access
_compiled_graph: Optional[StateGraph[AgentState]] = None

def get_compiled_graph() -> StateGraph[AgentState]:
    """
    Get singleton instance of compiled graph.
    
    Returns cached graph instance to avoid recompilation. Useful for
    long-running applications where the same graph is reused.
    
    Returns:
        Compiled LangGraph agent instance.
    """
    global _compiled_graph
    
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    
    return _compiled_graph