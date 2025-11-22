from abc import ABC, abstractmethod
from typing import Type, Any
from pydantic import BaseModel
from langchain_core.tools import StructuredTool

class BMO_skill(ABC):
    name: str
    description: str
    args_schema: Type[BaseModel]

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """Execute the skill logic."""
        pass

    def to_langchain_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=self.run,
            name=self.name,
            description=self.description,
            args_schema=self.args_schema,
        )
