import logging
from abc import ABC, abstractmethod
from typing import Type, Any, Dict, Optional, ClassVar, List
from pydantic import BaseModel, ValidationError
from langchain_core.tools import BaseTool, StructuredTool

# Configure logger
logger = logging.getLogger(__name__)


class BMO_skill(ABC):
    """
    Abstract base class for all BMO skills.
    
    Skills are reusable capabilities that the BMO assistant can use to
    interact with external systems, perform computations, or access data.
    Each skill must define its name, description, argument schema, and
    execution logic.
    
    Attributes:
        name: Unique identifier for the skill (should be snake_case).
        description: Clear, concise explanation of what the skill does.
        args_schema: Pydantic model defining the skill's input parameters.
        version: Optional version string for skill tracking.
        requires_auth: Whether the skill requires authentication.
        
    Example:
        >>> class CalculatorSkill(BMO_skill):
        ...     name = "calculator"
        ...     description = "Perform basic arithmetic operations"
        ...     args_schema = CalculatorInput
        ...
        ...     def run(self, operation: str, a: float, b: float) -> float:
        ...         if operation == "add":
        ...             return a + b
        ...         elif operation == "subtract":
        ...             return a - b
    """
    
    name: ClassVar[str]
    description: ClassVar[str]
    args_schema: ClassVar[Type[BaseModel]]
    version: ClassVar[str] = "1.0.0"
    requires_auth: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Validate subclass configuration when a skill is defined.
        
        Args:
            **kwargs: Additional keyword arguments passed to subclass.
            
        Raises:
            TypeError: If required class variables are not properly defined.
        """
        super().__init_subclass__(**kwargs)
        
        required_attrs: List[str] = ['name', 'description', 'args_schema']
        for attr in required_attrs:
            if not hasattr(cls, attr):
                raise TypeError(
                    f"Skill '{cls.__name__}' must define class variable '{attr}'"
                )
        
        # Validate specific attribute types and constraints
        if not isinstance(cls.name, str) or not cls.name:
            raise TypeError(f"Skill '{cls.__name__}' must have a non-empty string 'name'")
        
        if not isinstance(cls.description, str) or not cls.description:
            raise TypeError(f"Skill '{cls.__name__}' must have a non-empty string 'description'")
        
        if not issubclass(cls.args_schema, BaseModel):
            raise TypeError(f"Skill '{cls.__name__}' must have a Pydantic BaseModel as 'args_schema'")
        
        logger.debug(f"Successfully validated skill: {cls.name}")

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """
        Execute the core logic of the skill.
        
        This method must be implemented by all concrete skill classes.
        It should contain the main functionality and return meaningful
        results that can be used by the assistant.
        
        Args:
            **kwargs: Input parameters defined by the skill's args_schema.
                     Validated according to the Pydantic model before
                     reaching this method.
        
        Returns:
            The result of the skill execution. Can be any serializable type.
            
        Raises:
            Exception: Skill-specific exceptions should be documented by
                      concrete implementations. Common exceptions include
                      ValueError, ConnectionError, PermissionError, etc.
                      
        Note:
            Implementations should handle their own errors and provide
            meaningful error messages when possible.
        """
        pass

    def validate_input(self, **kwargs: Any) -> BaseModel:
        """
        Validate input parameters against the skill's argument schema.
        
        Args:
            **kwargs: Input parameters to validate.
            
        Returns:
            Validated Pydantic model instance.
            
        Raises:
            ValidationError: If input parameters don't conform to the schema.
        """
        try:
            logger.debug(f"Validating input for skill '{self.name}': {kwargs}")
            validated_input: BaseModel = self.args_schema(**kwargs)
            return validated_input
        except ValidationError as e:
            logger.error(f"Input validation failed for skill '{self.name}': {e}")
            raise

    def safe_run(self, **kwargs: Any) -> Any:
        """
        Execute the skill with input validation and error handling.
        
        This wrapper method provides a safe way to execute skills by
        validating inputs and catching exceptions. Useful for runtime
        execution where skill failures should not crash the entire system.
        
        Args:
            **kwargs: Input parameters for the skill.
            
        Returns:
            Skill execution result or error message.
        """
        try:
            # Validate input before execution
            self.validate_input(**kwargs)
            
            # Execute the skill
            logger.info(f"Executing skill: {self.name}")
            result: Any = self.run(**kwargs)
            
            logger.debug(f"Skill '{self.name}' executed successfully")
            return result
            
        except ValidationError as e:
            error_msg: str = f"Invalid input for skill '{self.name}': {e}"
            logger.warning(error_msg)
            return error_msg
            
        except Exception as e:
            error_msg: str = f"Skill '{self.name}' execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    def to_langchain_tool(self) -> BaseTool:
        """
        Convert this skill to a LangChain StructuredTool.
        
        Returns:
            A LangChain tool instance that can be used in LangChain
            agents and chains.
            
        Example:
            >>> skill = CalculatorSkill()
            >>> tool = skill.to_langchain_tool()
            >>> agent = initialize_agent([tool], llm)
        """
        try:
            tool: BaseTool = StructuredTool.from_function(
                func=self.safe_run,
                name=self.name,
                description=self.description,
                args_schema=self.args_schema,
            )
            
            logger.debug(f"Successfully converted skill '{self.name}' to LangChain tool")
            return tool
            
        except Exception as e:
            logger.error(f"Failed to convert skill '{self.name}' to LangChain tool: {e}")
            raise RuntimeError(f"Tool conversion failed for skill '{self.name}'") from e

    def get_skill_info(self) -> Dict[str, Any]:
        """
        Get metadata information about the skill.
        
        Returns:
            Dictionary containing skill metadata for registration,
            documentation, and debugging purposes.
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "requires_auth": self.requires_auth,
            "args_schema": self.args_schema.schema(),
            "class_name": self.__class__.__name__,
        }

    def __str__(self) -> str:
        """String representation of the skill for debugging."""
        return f"BMO_skill(name='{self.name}', version='{self.version}')"

    def __repr__(self) -> str:
        """Detailed representation of the skill."""
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"description='{self.description[:50]}...', "
                f"args_schema={self.args_schema.__name__})")


class SkillExecutionError(Exception):
    """
    Custom exception for skill execution failures.
    
    This exception should be raised by skill implementations when
    they encounter errors that should be handled specifically by
    the skill execution framework.
    """
    
    def __init__(self, skill_name: str, message: str, original_error: Optional[Exception] = None):
        self.skill_name: str = skill_name
        self.message: str = message
        self.original_error: Optional[Exception] = original_error
        super().__init__(f"Skill '{skill_name}' failed: {message}")


def create_skill_tool(skill_instance: BMO_skill) -> BaseTool:
    """
    Factory function to create a LangChain tool from a skill instance.
    
    Args:
        skill_instance: Instantiated BMO skill.
        
    Returns:
        Configured LangChain tool.
        
    Raises:
        TypeError: If the provided instance is not a BMO_skill.
    """
    if not isinstance(skill_instance, BMO_skill):
        raise TypeError(f"Expected BMO_skill instance, got {type(skill_instance)}")
    
    return skill_instance.to_langchain_tool()