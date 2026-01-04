from typing import List, Type
from src.BMO.skills.base import BMO_skill
from src.BMO.skills.collection.system_ops import SystemInfoSkill, SystemManagerFilesSkill
from src.BMO.skills.collection.web_search import WebSearchSkill

# List of allowed skill classes for explicit registration
SKILL_CLASSES: List[Type[BMO_skill]] = [
    SystemInfoSkill,
    SystemManagerFilesSkill,
    WebSearchSkill
]
