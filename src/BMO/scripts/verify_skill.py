import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.BMO.skills.registry import registry, load_manifest

# Explicitly load manifest
load_manifest()

def verify(skill_name):
    print("Verifying Skill Registration...")
    tools = registry.get_tools_list()
    tool_names = [t.name for t in tools]
    print(f"Registered tools: {tool_names}")
    
    if skill_name in tool_names:
        print(f"SUCCESS: '{skill_name}' is registered.")
        
        # Test execution with appropriate arguments
        skill = registry.skills[skill_name]
        try:
            if skill_name == "get_system_info":
                result = skill.run(query="Test Query")
            elif skill_name == "web_search":
                result = skill.run(query="Test Query")
            elif skill_name == "system_manager_files":
                result = skill.run(path="test_bmo_verify.txt", action="create", content="Verification test")
                # Clean up
                skill.run(path="test_bmo_verify.txt", action="delete")
            else:
                result = "No test case for this skill"
            
            print(f"Skill Execution Result: {result}")
        except Exception as e:
            print(f"FAILURE: Skill execution failed: {e}")
            sys.exit(1)
    else:
        print(f"FAILURE: '{skill_name}' is NOT registered.")
        sys.exit(1)

if __name__ == "__main__":
    tools = registry.get_tools_list()
    tool_names = [t.name for t in tools]
    for name in tool_names:
        verify(name)
        print("-" * 20)
