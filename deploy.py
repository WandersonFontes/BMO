import vertexai, os, logging
from vertexai.preview import reasoning_engines
from src.BMO.vertex_wrapper import BMOAgentWrapper

# 1. Configuration
PROJECT_ID = "gran-degravacoes-homologacao"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://bmo_assistant"
API_KEY_NAME = "OPENAI_API_KEY"

# --- SECURITY CHECK ---
# Retrieves the key from your local terminal to send to the cloud
api_key_value = os.getenv(API_KEY_NAME)
if not api_key_value:
    logging.error(f"❌ CRITICAL ERROR: The variable '{API_KEY_NAME}' was not found.")
    logging.error("👉 Before running this script, execute in your terminal:")
    logging.error(f'   export {API_KEY_NAME}="your-key-here" (Linux/Mac)')
    logging.error(f'   $env:{API_KEY_NAME}="your-key-here" (Windows PowerShell)')
    exit(1)

# Initialize SDK
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

# 2. Deploy
logging.info("Starting BMO Agent deployment to Vertex AI...")

try:
    remote_agent = reasoning_engines.ReasoningEngine.create(
        BMOAgentWrapper(), # Instantiate your wrapper class
        requirements=[
            "langchain>=1.0.8,<2.0.0",
            "langchain-community>=0.4.1,<0.5.0",
            "langchain-openai>=1.0.3,<2.0.0",
            "litellm>=1.80.0,<2.0.0",
            "pydantic>=2.12.4,<3.0.0",
            "pydantic-settings>=2.12.0,<3.0.0",
            "python-dotenv>=1.2.1,<2.0.0",
            "langchain-litellm>=0.3.2,<0.4.0",
            "langgraph>=1.0.5,<2.0.0",
            "google-cloud-aiplatform[reasoningengine]>=1.130.0,<2.0.0"
        ],
        extra_packages=["./src"],
        display_name="BMO Assistant",
        description="LangGraph Agent for BMO Assistant",
    )

    logging.info("Deployment completed!")
    logging.info(f"Agent ID: {remote_agent.resource_name}")
except Exception as e:
    logging.error(f"❌ CRITICAL ERROR: {str(e)}")