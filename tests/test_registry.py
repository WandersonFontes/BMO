import pytest
from src.BMO.skills.registry import SkillRegistry
from src.BMO.skills.base import BMO_skill
from pydantic import BaseModel

class MockSkill(BMO_skill):
    name = "mock_skill"
    description = "A mock skill for testing"
    args_schema = BaseModel
    def run(self, **kwargs): return "done"

def test_registry_singleton():
    reg1 = SkillRegistry()
    reg2 = SkillRegistry()
    assert reg1 is reg2

def test_register_skill(clean_registry):
    skill = MockSkill()
    assert clean_registry.register(skill) is True
    assert "mock_skill" in clean_registry.skills
    assert clean_registry.get_skill("mock_skill") is skill

def test_register_duplicate_skill(clean_registry):
    skill = MockSkill()
    clean_registry.register(skill)
    with pytest.raises(ValueError, match="already registered"):
        clean_registry.register(skill)

def test_unregister_skill(clean_registry):
    skill = MockSkill()
    clean_registry.register(skill)
    assert clean_registry.unregister("mock_skill") is True
    assert "mock_skill" not in clean_registry.skills

def test_get_tools_list(clean_registry):
    skill = MockSkill()
    clean_registry.register(skill)
    tools = clean_registry.get_tools_list()
    assert len(tools) == 1
    assert tools[0].name == "mock_skill"
