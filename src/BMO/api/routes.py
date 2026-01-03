from fastapi import APIRouter, HTTPException, Path
from typing import List, Dict, Any
import logging
import uuid
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.BMO.api.schemas import ChatRequest, ChatResponse, HistoryResponse, MessageHistory, HealthResponse
from src.BMO.config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a user message and return the AI response.
    
    This endpoint:
    1. Initializes/retreives a session.
    2. Invokes the LangGraph workflow.
    3. Persists the conversation via the graph's checkpointer.
    """
    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"API Chat request - Session: {session_id}")
    
    try:
        from src.BMO.orchestrator.supervisor import Supervisor
        supervisor = Supervisor()
        
        # Invoke the A2A supervisor
        final_state = await supervisor.ainvoke(request.message)
        
        # Reconstruct response string 
        steps = final_state.get("plan").steps if final_state.get("plan") else []
        step_results = final_state.get("step_results", {})
        
        summary = []
        for step in steps:
             result = step_results.get(step.step_id)
             if result:
                 # Extract content or summary
                 text = result.output.get('content', result.output.get('summary', str(result.output)))
                 summary.append(text)
        
        response_text = "\n\n".join(summary) if summary else "I couldn't generate a specific response."

        return ChatResponse(
            response=response_text,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error in /chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str = Path(..., description="The session ID to retrieve history for")):
    """Retrieve message history for a specific session."""
    # TODO: Implement persistence for the new A2A AgentState
    return HistoryResponse(
        session_id=session_id,
        messages=[]
    )

@router.get("/health", response_model=HealthResponse)
async def health():
    """Check API and system health."""
    return HealthResponse(
        status="ok",
        version="0.1.0"
    )
