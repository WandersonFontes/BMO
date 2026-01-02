import logging
import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ValidationError
from ddgs import DDGS

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
    Skill to perform web searches for current information using DuckDuckGo.
    
    This skill enables the assistant to search for real-time information,
    recent news, and current data that may not be in its training knowledge.
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
        self._search_providers = ["duckduckgo"]
        self._max_results = 5

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
        Execute web search for the given query using DuckDuckGo (ddgs).
        
        Args:
            query: The search term or question to look up.
            
        Returns:
            Search results as a formatted string.
            
        Raises:
            ValidationError: If the query fails validation checks.
        """
        # Validate input
        validation_error = self._validate_query(query)
        if validation_error:
            logger.warning(f"Invalid search query: {query} - {validation_error}")
            return f"Search error: {validation_error}"

        logger.info(f"Executing web search for query: '{query}'")
        
        try:
            results = []
            
            # Heuristic for time-sensitive queries
            timelimit = None
            time_keywords = ["hoje", "agora", "today", "now", "current", "atual"]
            if any(word in query.lower() for word in time_keywords):
                timelimit = "d"  # Past day
            
            with DDGS() as ddgs:
                # Use the 'text' method with region and timelimit
                # Note: query is a positional argument in ddgs>=9.x
                search_results = ddgs.text(
                    query,
                    region="br-pt",  # Focus on Brazil/Portuguese results
                    safesearch="moderate",
                    timelimit=timelimit,
                    max_results=self._max_results
                )
                
                if search_results:
                    for r in search_results:
                        results.append({
                            "title": r.get("title", "No Title"),
                            "snippet": r.get("body", "No content"),
                            "link": r.get("href", "#")
                        })
            
            if not results:
                return f"No results found for query: '{query}'"

            # Format results for LLM consumption
            formatted_output = f"Search Results for '{query}':\n\n"
            for i, res in enumerate(results, 1):
                formatted_output += f"{i}. {res['title']}\n"
                formatted_output += f"   Source: {res['link']}\n"
                formatted_output += f"   Summary: {res['snippet']}\n\n"
                
            logger.debug(f"Search completed for query: '{query}', found {len(results)} results")
            return formatted_output
            
        except Exception as e:
            error_msg = f"Search operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"Search error: Unable to complete search at this time. Please try again later. Error: {str(e)}"

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