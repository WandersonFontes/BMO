import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.BMO.skills.registry import registry

# Import to register
import src.BMO.skills.collection.system_ops
import src.BMO.skills.collection.web_search

def verify(skill_name):
    print("Verifying Skill Registration...")
    tools = registry.get_tools_list()
    tool_names = [t.name for t in tools]
    print(f"Registered tools: {tool_names}")
    
    if skill_name in tool_names:
        print(f"SUCCESS: '{skill_name}' is registered.")
        
        # Test execution
        skill = registry.skills[skill_name]
        result = skill.run(query="Test Query")
        print(f"Skill Execution Result: {result}")
    else:
        print(f"FAILURE: '{skill_name}' is NOT registered.")
        sys.exit(1)

if __name__ == "__main__":
    verify("get_system_info")
