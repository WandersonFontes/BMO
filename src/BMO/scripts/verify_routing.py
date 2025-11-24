import sys
import os
import uuid
from langchain_core.messages import HumanMessage

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.BMO.core.orchestrator import build_graph

def verify_routing():
    print("Verifying Graph Routing...")
    try:
        app = build_graph()
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        # Test simple greeting (should NOT trigger tools, just go to END)
        user_input = "Oi"
        print(f"Sending query: {user_input}")
        
        inputs = {"messages": [HumanMessage(content=user_input)]}
        result = app.invoke(inputs, config=config)
        
        last_message = result["messages"][-1]
        print(f"Agent Response: {last_message.content}")
        
        if last_message.content:
             print("SUCCESS: Agent responded without routing error.")
        else:
             print("WARNING: Empty response.")

    except Exception as e:
        print(f"FAILED: Agent execution error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_routing()
