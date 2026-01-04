import logging
from typing import Dict, List, Optional, Iterator, Tuple, Any
from langchain_core.tools import BaseTool, StructuredTool

from src.BMO.skills.base import BMO_skill

# Configure logger
logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Singleton registry for managing BMO skills.
    
    The registry provides a centralized repository for all available skills,
    enabling skill discovery, tool conversion, and lifecycle management.
    Implements the singleton pattern to ensure consistent state across the application.
    
    Attributes:
        skills: Dictionary mapping skill names to skill instances.
        _initialized: Flag indicating whether the registry has been initialized.
        
    Example:
        >>> registry = SkillRegistry()
        >>> skill = SystemInfoSkill()
        >>> registry.register(skill)
        >>> tools = registry.get_tools_list()
    """
    
    _instance: Optional['SkillRegistry'] = None
    _initialized: bool = False

    def __new__(cls) -> 'SkillRegistry':
        """
        Create or return the singleton instance.
        
        Returns:
            Singleton SkillRegistry instance.
        """
        if cls._instance is None:
            cls._instance = super(SkillRegistry, cls).__new__(cls)
            cls._instance.skills: Dict[str, BMO_skill] = {}
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """
        Initialize the registry instance.
        
        Prevents reinitialization of the singleton instance while allowing
        subclassing and potential future extensibility.
        """
        if not self._initialized:
            self.skills: Dict[str, BMO_skill] = {}
            self._initialized: bool = True
            logger.info("SkillRegistry initialized")

    def register(self, skill: BMO_skill, overwrite: bool = False) -> bool:
        """
        Register a new skill with the registry.
        
        Args:
            skill: The skill instance to register.
            overwrite: Whether to overwrite an existing skill with the same name.
                      Defaults to False to prevent accidental overwrites.
        
        Returns:
            True if registration was successful, False otherwise.
            
        Raises:
            TypeError: If the provided object is not a BMO_skill instance.
            ValueError: If skill name is already registered and overwrite is False.
            
        Example:
            >>> registry = SkillRegistry()
            >>> skill = CalculatorSkill()
            >>> success = registry.register(skill)
            True
        """
        if not isinstance(skill, BMO_skill):
            error_msg: str = f"Can only register BMO_skill instances, got {type(skill)}"
            logger.error(error_msg)
            raise TypeError(error_msg)

        skill_name: str = skill.name
        
        if skill_name in self.skills and not overwrite:
            error_msg: str = f"Skill '{skill_name}' already registered. Use overwrite=True to replace."
            logger.warning(error_msg)
            raise ValueError(error_msg)

        if skill_name in self.skills:
            logger.warning(f"Overwriting previously registered skill: '{skill_name}'")
        
        self.skills[skill_name] = skill
        logger.info(f"Registered skill: '{skill_name}' - {skill.description}")
        return True

    def unregister(self, skill_name: str) -> bool:
        """
        Remove a skill from the registry.
        
        Args:
            skill_name: Name of the skill to remove.
            
        Returns:
            True if skill was found and removed, False otherwise.
            
        Example:
            >>> registry.unregister("calculator")
            True
        """
        if skill_name in self.skills:
            del self.skills[skill_name]
            logger.info(f"Unregistered skill: '{skill_name}'")
            return True
        else:
            logger.warning(f"Attempted to unregister non-existent skill: '{skill_name}'")
            return False

    def get_skill(self, skill_name: str) -> Optional[BMO_skill]:
        """
        Retrieve a skill by name.
        
        Args:
            skill_name: Name of the skill to retrieve.
            
        Returns:
            Skill instance if found, None otherwise.
        """
        skill: Optional[BMO_skill] = self.skills.get(skill_name)
        if skill:
            logger.debug(f"Retrieved skill: '{skill_name}'")
        else:
            logger.debug(f"Skill not found: '{skill_name}'")
        return skill

    def get_tools_list(self) -> List[BaseTool]:
        """
        Convert all registered skills to LangChain tools.
        
        Returns:
            List of LangChain tools ready for use in agents and chains.
            
        Raises:
            RuntimeError: If tool conversion fails for any registered skill.
            
        Example:
            >>> tools = registry.get_tools_list()
            >>> agent = initialize_agent(tools, llm)
        """
        tools: List[BaseTool] = []
        conversion_errors: List[str] = []
        
        for skill_name, skill in self.skills.items():
            try:
                tool: BaseTool = skill.to_langchain_tool()
                tools.append(tool)
                logger.debug(f"Successfully converted skill '{skill_name}' to tool")
            except Exception as e:
                error_msg: str = f"Failed to convert skill '{skill_name}' to tool: {e}"
                logger.error(error_msg)
                conversion_errors.append(error_msg)
        
        if conversion_errors and not tools:
            # All conversions failed
            raise RuntimeError(
                f"All skill conversions failed: {', '.join(conversion_errors)}"
            )
        elif conversion_errors:
            # Some conversions failed, but we have some tools
            logger.warning(
                f"Some skill conversions failed, returning {len(tools)}/{len(self.skills)} tools. "
                f"Errors: {', '.join(conversion_errors)}"
            )
        
        logger.info(f"Converted {len(tools)} skills to LangChain tools")
        return tools

    def get_skill_names(self) -> List[str]:
        """
        Get names of all registered skills.
        
        Returns:
            Sorted list of skill names.
        """
        names: List[str] = sorted(self.skills.keys())
        logger.debug(f"Retrieved {len(names)} skill names")
        return names

    def get_skills_info(self) -> List[Dict[str, Any]]:
        """
        Get metadata for all registered skills.
        
        Returns:
            List of dictionaries containing skill metadata.
        """
        info_list: List[Dict[str, Any]] = []
        for skill in self.skills.values():
            try:
                skill_info: Dict[str, Any] = skill.get_skill_info()
                info_list.append(skill_info)
            except Exception as e:
                logger.warning(f"Failed to get info for skill '{skill.name}': {e}")
                # Provide basic info even if get_skill_info fails
                info_list.append({
                    "name": skill.name,
                    "description": skill.description,
                    "error": f"Failed to retrieve full info: {e}"
                })
        
        logger.debug(f"Retrieved metadata for {len(info_list)} skills")
        return info_list

    def skill_exists(self, skill_name: str) -> bool:
        """
        Check if a skill is registered.
        
        Args:
            skill_name: Name of the skill to check.
            
        Returns:
            True if skill exists, False otherwise.
        """
        exists: bool = skill_name in self.skills
        logger.debug(f"Skill '{skill_name}' exists: {exists}")
        return exists

    def clear_registry(self) -> None:
        """
        Remove all skills from the registry.
        
        Useful for testing or application reset scenarios.
        """
        skill_count: int = len(self.skills)
        self.skills.clear()
        logger.info(f"Cleared registry, removed {skill_count} skills")

    def count_skills(self) -> int:
        """
        Get the number of registered skills.
        
        Returns:
            Number of skills in the registry.
        """
        count: int = len(self.skills)
        logger.debug(f"Registry contains {count} skills")
        return count

    def load_manifest(self) -> int:
        """
        Explicitly load and register skills from the registry manifest.
        
        This replaces the dynamic discovery mechanism with explicit dependency injection,
        improving security, reliability, and supporting tree shaking.
        
        Returns:
            Number of skills successfully registered from the manifest.
        """
        from .registry_manifest import SKILL_CLASSES
        
        logger.info(f"Starting explicit skill registration from manifest")
        registered_count = 0
        
        for skill_cls in SKILL_CLASSES:
            try:
                skill_instance = skill_cls()
                if self.register(skill_instance):
                    registered_count += 1
            except Exception as e:
                logger.error(f"Failed to register skill class {skill_cls.__name__}: {e}")
        
        logger.info(f"Manifest loading completed. Registered {registered_count} skills.")
        return registered_count

    def __iter__(self) -> Iterator[Tuple[str, BMO_skill]]:
        """
        Allow iteration over registered skills.
        
        Returns:
            Iterator yielding (skill_name, skill_instance) tuples.
        """
        return iter(self.skills.items())

    def __contains__(self, skill_name: str) -> bool:
        """
        Check if a skill is registered using 'in' operator.
        
        Args:
            skill_name: Name of the skill to check.
            
        Returns:
            True if skill exists, False otherwise.
        """
        return skill_name in self.skills

    def __len__(self) -> int:
        """
        Get the number of registered skills using len().
        
        Returns:
            Number of skills in the registry.
        """
        return len(self.skills)

    def __str__(self) -> str:
        """String representation of the registry."""
        return f"SkillRegistry(skills={len(self.skills)})"

    def __repr__(self) -> str:
        """Detailed representation of the registry."""
        skill_names: list = list(self.skills.keys())
        return f"SkillRegistry(skills={skill_names})"

# Global registry instance
registry: SkillRegistry = SkillRegistry()

def get_registry() -> SkillRegistry:
    """
    Get the global skill registry instance.
    
    Returns:
        Global SkillRegistry singleton instance.
        
    Example:
        >>> registry = get_registry()
        >>> registry.register(my_skill)
    """
    return registry

def register_skill(skill: BMO_skill, overwrite: bool = False) -> bool:
    """
    Convenience function to register a skill with the global registry.
    
    Args:
        skill: The skill instance to register.
        overwrite: Whether to overwrite existing skill with same name.
        
    Returns:
        True if registration successful.
    """
    return registry.register(skill, overwrite)

def get_available_tools() -> List[BaseTool]:
    """
    Convenience function to get all tools from the global registry.
    
    Returns:
        List of LangChain tools from all registered skills.
    """
    return registry.get_tools_list()

def load_manifest() -> int:
    """
    Convenience function to trigger explicit skill registration on the global registry.
    
    Returns:
        Number of skills registered.
    """
    return registry.load_manifest()