from src.BMO.core.orchestrator import get_compiled_graph
from langchain_core.messages import HumanMessage
import vertexai.preview.reasoning_engines as reasoning_engines

class BMOAgentWrapper:
    def __init__(self):
        self.graph = get_compiled_graph()

    def query(self, message: str, thread_id: str = "1") -> str:
        config = {"configurable": {"thread_id": thread_id}}
        
        inputs = {"messages": [HumanMessage(content=message)]}
        result = self.graph.invoke(inputs, config)
        
        last_message = result["messages"][-1]
        return last_message.content