import sys
import os
import uuid
from langchain_core.messages import HumanMessage

# Add src to pythonpath
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.BMO.core.orchestrator import build_graph

def test_persistence():
    session_id = f"test-session-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}
    
    print(f"--- Session 1: Starting with thread_id: {session_id} ---")
    graph1 = build_graph()
    
    # Send first message
    print("User: Meu nome é Aang e eu moro em Ba Sing Se.")
    input1 = {"messages": [HumanMessage(content="Meu nome é Aang e eu moro em Ba Sing Se.")]}
    for event in graph1.stream(input1, config, stream_mode="values"):
        pass # Wait for completion
        
    print("Session 1 finished and closed.")
    
    print(f"\n--- Session 2: Reopening with same thread_id: {session_id} ---")
    # Re-build graph to simulate application restart
    graph2 = build_graph()
    
    print("User: Qual é o meu nome e onde eu moro?")
    input2 = {"messages": [HumanMessage(content="Qual é o meu nome e onde eu moro?")]}
    
    final_message = ""
    for event in graph2.stream(input2, config, stream_mode="values"):
        if "messages" in event:
            final_message = event["messages"][-1].content
            
    print(f"BMO: {final_message}")
    
    if "Aang" in final_message and "Ba Sing Se" in final_message:
        print("\n✅ Verification SUCCESS: BMO remembered the information across sessions!")
    else:
        print("\n❌ Verification FAILED: BMO forgot the information.")

if __name__ == "__main__":
    test_persistence()
