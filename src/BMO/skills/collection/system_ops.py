import platform
import datetime
from pydantic import BaseModel, Field
from src.BMO.skills.base import BMO_skill
from src.BMO.skills.registry import registry

class SystemInfoInput(BaseModel):
    query: str = Field(description="The specific information requested about the system (optional).")

class SystemInfoSkill(BMO_skill):
    name = "get_system_info"
    description = "Returns information about the operating system and current time."
    args_schema = SystemInfoInput

    def run(self, query: str = "") -> str:
        os_info = platform.system() + " " + platform.release()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"OS: {os_info}, Time: {current_time}"

# Auto-register the skill
registry.register(SystemInfoSkill())
