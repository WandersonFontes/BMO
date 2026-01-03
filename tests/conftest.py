import pytest
import os
import sys

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

@pytest.fixture(scope="session")
def test_session_id():
    """Fixture to provide a consistent session ID for tests."""
    return "test-session-uuid"

@pytest.fixture
def clean_registry():
    """Fixture to clear the skill registry before each test."""
    from src.BMO.skills.registry import registry
    registry.clear_registry()
    yield registry
    registry.clear_registry()
