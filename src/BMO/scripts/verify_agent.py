import sys
import os
import uuid
from langchain_core.messages import HumanMessage

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.BMO.core.orchestrator import build_graph

def verify_agent():
    print("Initializing Agent Graph...")
    try:
        app = build_graph()
    except Exception as e:
        print(f"FAILED to build graph: {e}")
        sys.exit(1)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Test query that triggers a tool (System Info)
    user_input = "Qual é o SO desse computador?"
    print(f"Sending query: {user_input}")
    
    inputs = {"messages": [HumanMessage(content=user_input)]}
    
    try:
        # We use stream to see events, or invoke for final result. 
        # Invoke is safer to catch the specific error we saw.
        result = app.invoke(inputs, config=config)
        
        last_message = result["messages"][-1]
        print(f"Agent Response: {last_message.content}")
        
        if "Linux" in last_message.content or "OS:" in last_message.content:
            print("SUCCESS: Agent successfully used the tool and responded.")
        else:
            print("WARNING: Agent responded but might not have used the tool correctly. Check output.")
            
    except Exception as e:
        print(f"FAILED: Agent execution error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_agent()
