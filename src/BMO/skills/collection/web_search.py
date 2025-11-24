import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ValidationError

from src.BMO.skills.base import BMO_skill
from src.BMO.skills.registry import registry

# Configure logger
logger = logging.getLogger(__name__)


class SearchInput(BaseModel):
    """
    Input model for web search queries.
    
    Attributes:
        query: The search term or question to look up on the internet.
               Should be specific and well-formed for best results.
    """
    query: str = Field(
        description="The exact term or question to search for on the internet.",
        min_length=1,
        max_length=500,
        examples=["current weather in New York", "Python 3.13 new features", "latest AI research papers"]
    )


class WebSearchSkill(BMO_skill):
    """
    Skill to perform web searches for current information.
    
    This skill enables the assistant to search for real-time information,
    recent news, and current data that may not be in its training knowledge.
    Can be extended with actual search API implementations.
    """
    
    name: str = "web_search"
    description: str = (
        "Search the internet for current information, recent news, or real-time data "
        "that the assistant doesn't know. Use for time-sensitive queries or topics "
        "that require up-to-date information."
    )
    args_schema: type[BaseModel] = SearchInput

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the web search skill.
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self._search_providers = ["duckduckgo", "google", "bing"]
        self._max_results = 5

    def _simulate_search(self, query: str) -> str:
        """
        Simulate web search results for development and testing.
        
        In a production environment, this would be replaced with actual
        search API calls to providers like DuckDuckGo, Serper, or others.
        
        Args:
            query: The search query to simulate.
            
        Returns:
            Simulated search results with relevant mock data.
        """
        # Common query patterns and their simulated responses
        query_patterns: Dict[str, str] = {
            "python": (
                f"Search results for '{query}': Python 3.13 includes new features for better error messages, "
                "performance improvements in the interpreter, and enhanced type system. The latest release "
                "focuses on developer productivity and runtime efficiency."
            ),
            "weather": (
                f"Search results for '{query}': Current weather information shows mild conditions across "
                "most regions. For specific locations, real-time weather APIs would provide precise "
                "temperature, precipitation, and forecast data."
            ),
            "news": (
                f"Search results for '{query}': Top news stories cover technology advancements, "
                "global events, and economic developments. Real search would provide current "
                "headlines from reputable news sources."
            ),
            "ai": (
                f"Search results for '{query}': Recent AI developments include new language models, "
                "computer vision breakthroughs, and ethical AI discussions. The field continues "
                "to evolve rapidly with new research papers weekly."
            )
        }
        
        # Find the best matching pattern or return generic response
        query_lower = query.lower()
        for pattern, response in query_patterns.items():
            if pattern in query_lower:
                return response
        
        # Generic response for unmatched queries
        return (
            f"Search results for '{query}': Found multiple relevant sources discussing this topic. "
            "In a production environment, this would return actual web search results with "
            "summaries and links to current information from reliable sources."
        )

    def _validate_query(self, query: str) -> Optional[str]:
        """
        Validate the search query for common issues.
        
        Args:
            query: The search query to validate.
            
        Returns:
            Error message if validation fails, None otherwise.
        """
        if not query or not query.strip():
            return "Search query cannot be empty"
        
        if len(query.strip()) < 2:
            return "Search query is too short. Please provide more specific terms."
        
        if len(query) > 500:
            return "Search query is too long. Please shorten your query."
            
        return None

    def run(self, query: str) -> str:
        """
        Execute web search for the given query.
        
        Args:
            query: The search term or question to look up.
            
        Returns:
            Search results as a formatted string. In simulation mode, returns
            mock data. In production, would return actual search results.
            
        Raises:
            ValidationError: If the query fails validation checks.
            
        Example:
            >>> skill.run("Python 3.13 features")
            'Search results for "Python 3.13 features": ...'
        """
        # Validate input
        validation_error = self._validate_query(query)
        if validation_error:
            logger.warning(f"Invalid search query: {query} - {validation_error}")
            return f"Search error: {validation_error}"

        logger.info(f"Executing web search for query: '{query}'")
        
        try:
            # In a real implementation, this would call actual search APIs
            # For now, we simulate the search behavior
            results = self._simulate_search(query)
            
            logger.debug(f"Search completed for query: '{query}'")
            return results
            
        except Exception as e:
            error_msg = f"Search operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"Search error: Unable to complete search at this time. Please try again later."

    def get_search_providers(self) -> list[str]:
        """
        Get available search providers.
        
        Returns:
            List of supported search provider names.
        """
        return self._search_providers.copy()

    def set_max_results(self, max_results: int) -> None:
        """
        Set maximum number of search results to return.
        
        Args:
            max_results: Maximum number of results (1-20).
        """
        if 1 <= max_results <= 20:
            self._max_results = max_results
        else:
            logger.warning(f"Invalid max_results value: {max_results}. Must be between 1-20.")


# Auto-register the skill with the registry
registry.register(WebSearchSkill())