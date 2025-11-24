# How to Add New Skills to BMO

This guide explains how to extend BMO's capabilities by adding new "Skills".

## The Concept

Skills are the bridge between BMO's "brain" (the LLM) and the real world. They allow the assistant to execute actions, search for information, or interact with other systems.

In BMO, a Skill is a Python class that inherits from `BMO_skill` and is registered in the `registry`.

## Step-by-Step: Creating a Simple Skill

Let's create an example Skill that simulates an internet search.

### 1. Create the Skill File

Create a new file in `src/BMO/skills/collection/`, for example `web_search.py`.

### 2. Define the Structure

```python
from pydantic import BaseModel, Field
from src.BMO.skills.base import BMO_skill
from src.BMO.skills.registry import registry

# 1. Define input arguments (what the LLM needs to provide)
class SearchInput(BaseModel):
    query: str = Field(description="The exact term to search on the internet")

# 2. Create the Skill class
class WebSearchSkill(BMO_skill):
    name = "web_search"  # Unique tool name
    description = "Use this to search for current information on the internet."
    args_schema = SearchInput

    def run(self, query: str) -> str:
        # Tool logic
        print(f"--- Browsing the web for: {query} ---")
        return f"Simulated results for '{query}': Python 3.13 was released..."

# 3. Register the Skill
registry.register(WebSearchSkill())
```

### 3. Ensure it is Loaded

For BMO to "see" your new skill, the Python file must be imported. The easiest way is to ensure it is imported in `src/BMO/core/orchestrator.py` or through the `__init__.py` of the `collection` package.

If you add it to `src/BMO/skills/collection/__init__.py`:

```python
from .web_search import WebSearchSkill
```

And ensure that `src/BMO/core/orchestrator.py` imports from `src.BMO.skills.collection`, the skill will be registered automatically.

## Advanced Skills (Agents as Skills)

You can encapsulate entire agents within a Skill. This enables the "Hub-and-Spoke" pattern, where BMO (Hub) delegates complex tasks to specialist agents (Spokes).

Example structure for a Coding Agent:

```python
class CodingTaskInput(BaseModel):
    task_description: str = Field(description="Description of the code to be generated")

class PythonCoderSkill(BMO_skill):
    name = "senior_python_developer"
    description = "Specialist Python agent. Use for complex coding tasks."
    args_schema = CodingTaskInput

    def run(self, task_description: str) -> str:
        # Here you would invoke another LangGraph graph
        # result = coder_graph.invoke(...)
        return "Code generated successfully..."
```

## Summary

1. **Define Input**: Use `pydantic.BaseModel`.
2. **Implement Logic**: Inherit from `BMO_skill` and implement `run`.
3. **Register**: Use `registry.register()`.
4. **Import**: Ensure the file is read at startup.
