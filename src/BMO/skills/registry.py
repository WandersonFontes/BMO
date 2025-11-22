from typing import Dict, List
from langchain_core.tools import StructuredTool
from src.BMO.skills.base import BMO_skill

class SkillRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SkillRegistry, cls).__new__(cls)
            cls._instance.skills: Dict[str, BMO_skill] = {}
        return cls._instance

    def register(self, skill: BMO_skill) -> None:
        """Register a new skill."""
        if skill.name in self.skills:
            print(f"Warning: Skill '{skill.name}' already registered. Overwriting.")
        self.skills[skill.name] = skill

    def get_tools_list(self) -> List[StructuredTool]:
        """Convert all registered skills to LangChain tools."""
        return [skill.to_langchain_tool() for skill in self.skills.values()]

registry = SkillRegistry()
