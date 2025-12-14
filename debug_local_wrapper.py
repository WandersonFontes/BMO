import logging
import sys
from src.BMO.vertex_wrapper import BMOAgentWrapper
from src.BMO.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def test_wrapper():
    print("Initializing Wrapper...")
    try:
        wrapper = BMOAgentWrapper()
        
        print("Sending Query...")
        response = wrapper.query("Hello! Who are you?", thread_id="debug-session-1")
        
        print("\nResponse:")
        print(response)
        
    except Exception as e:
        print(f"\n❌ Local Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_wrapper()
