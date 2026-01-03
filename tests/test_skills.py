import pytest
from src.BMO.skills.collection.system_ops import SystemInfoSkill, SystemManagerFilesSkill
from pydantic import BaseModel

def test_system_info_skill():
    skill = SystemInfoSkill()
    assert skill.name == "get_system_info"
    result = skill.run()
    assert "OS:" in result
    assert "Time:" in result

def test_system_manager_files_skill_read_nonexistent(tmp_path):
    skill = SystemManagerFilesSkill()
    # Test reading a nonexistent file
    result = skill.run(action="read", path=str(tmp_path / "nonexistent.txt"))
    assert "Error" in result or "not found" in result.lower()

def test_system_manager_files_skill_write_read(tmp_path):
    skill = SystemManagerFilesSkill()
    test_file = str(tmp_path / "test.txt")
    test_content = "Hello World"
    
    # Write
    write_result = skill.run(action="write", path=test_file, content=test_content)
    assert "successfully" in write_result.lower()
    
    # Read
    read_result = skill.run(action="read", path=test_file)
    assert test_content in read_result

def test_system_manager_files_skill_delete(tmp_path):
    skill = SystemManagerFilesSkill()
    test_file = tmp_path / "to_delete.txt"
    test_file.write_text("content")
    
    delete_result = skill.run(action="delete", path=str(test_file))
    assert "deleted" in delete_result.lower()
    assert not test_file.exists()
