import uuid
from langchain_core.messages import HumanMessage
from src.BMO.core.orchestrator import build_graph

def main():
    # 1. Initialize the graph
    app = build_graph()
    
    # 2. Create a unique thread ID for this session
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"BMO Assistant Initialized (Session: {thread_id})")
    print("Type 'exit' or 'quit' to stop.")
    
    # 3. CLI Loop
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                print("BMO: Goodbye!")
                break
            
            # 4. Stream responses
            inputs = {"messages": [HumanMessage(content=user_input)]}
            for event in app.stream(inputs, config=config, stream_mode="values"):
                # Filter for the last message to avoid printing intermediate steps redundantly if not needed
                # However, app.stream with stream_mode="values" yields the full state.
                # We just want to print the last message if it's from the AI.
                message = event["messages"][-1]
                if message.type == "ai":
                    print(f"BMO: {message.content}")
                    
        except KeyboardInterrupt:
            print("\nBMO: Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
