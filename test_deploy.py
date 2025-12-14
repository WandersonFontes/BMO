import vertexai
from vertexai.preview import reasoning_engines

# Configuration
PROJECT_ID = "gran-degravacoes-homologacao"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://bmo_assistant"

# The Resource ID from your deployment output
# projects/645710854334/locations/us-central1/reasoningEngines/6425301861141577728
AGENT_RESOURCE_ID = "projects/645710854334/locations/us-central1/reasoningEngines/6425301861141577728"

# Initialize SDK
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

print(f"📡 Connecting to Agent: {AGENT_RESOURCE_ID}...")

try:
    # Load the remote agent
    remote_agent = reasoning_engines.ReasoningEngine(AGENT_RESOURCE_ID)
    
    # Test query
    query_text = "Hello! Who are you?"
    print(f"\nSending query: '{query_text}'")
    
    response = remote_agent.query(message=query_text, thread_id="debug-session-1")
    
    print("\n🤖 Agent Response:")
    print(response)

except Exception as e:
    print(f"\n❌ Error: {e}")
