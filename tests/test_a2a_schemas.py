import pytest
from uuid import uuid4
from src.BMO.agents.schemas import A2AMessage, AgentCapabilities, AgentResponse, ExecutionPlan, ExecutionStep, AgentState

def test_a2a_message_creation():
    msg = A2AMessage(
        correlation_id=uuid4(),
        from_agent="test_sender",
        to_agent="test_receiver",
        intent="test_intent",
        payload={"foo": "bar"}
    )
    assert msg.from_agent == "test_sender"
    assert msg.payload["foo"] == "bar"

def test_agent_capabilities():
    caps = AgentCapabilities(
        accepts_intents=["a", "b"],
        produces=["c"],
        requires=[]
    )
    assert "a" in caps.accepts_intents

def test_agent_response():
    resp = AgentResponse(
        status="success",
        output={"result": "ok"}
    )
    assert resp.status == "success"

def test_agent_state():
    state = AgentState(
        plan=ExecutionPlan(steps=[], strategy_rationale=""),
        step_results={},
        current_step=0,
        correlation_id=uuid4(),
        last_agent_output=None,
        retry_count=0,
        critic_feedback=None
    )
    assert state["current_step"] == 0
