from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    """Request model for AI chat interaction."""
    message: str = Field(..., description="Message from the user", example="Hello BMO!")
    session_id: Optional[str] = Field(None, description="Identifier for conversation persistence")

class ChatResponse(BaseModel):
    """Response model for AI chat interaction."""
    response: str = Field(..., description="Response message from the AI")
    session_id: str = Field(..., description="Identifier for the active session")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MessageHistory(BaseModel):
    """Model representing a single message in history."""
    role: str = Field(..., description="Role of the message author (human/ai/system)")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[datetime] = None

class HistoryResponse(BaseModel):
    """Response model for conversation history."""
    session_id: str
    messages: List[MessageHistory]

class HealthResponse(BaseModel):
    """Status model for health check."""
    status: str = "ok"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
