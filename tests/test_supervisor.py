import pytest
from unittest.mock import patch
from src.BMO.orchestrator.supervisor import Supervisor

@pytest.mark.asyncio
async def test_supervisor_init():
    with patch("src.BMO.orchestrator.supervisor.Planner"):
        # Patch the function that creates the LLM client
        with patch("src.BMO.core.llm.get_llm_client") as mock_get_llm:
            supervisor = Supervisor()
            assert supervisor.workflow is not None
