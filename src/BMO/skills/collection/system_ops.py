import platform
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError

from src.BMO.skills.base import BMO_skill
from src.BMO.skills.registry import registry


class SystemInfoInput(BaseModel):
    """Input model for system information queries."""
    query: Optional[str] = Field(
        default="",
        description="Specific information requested about the system. Currently supports basic OS and time information."
    )


class SystemManagerFilesInput(BaseModel):
    """Input model for file management operations."""
    path: str = Field(description="Absolute or relative path to the file.")
    action: str = Field(
        description="Action to perform on the file.",
        examples=["create", "delete", "read", "write"]
    )


class SystemInfoSkill(BMO_skill):
    """
    Skill to retrieve basic system information.
    
    This skill provides information about the operating system
    and current date/time in a standardized format.
    """
    
    name: str = "get_system_info"
    description: str = "Returns information about the operating system and current time."
    args_schema: type[BaseModel] = SystemInfoInput

    def run(self, query: str = "") -> str:
        """
        Execute the system information retrieval.
        
        Args:
            query: Optional query for specific system information.
                   Currently returns basic OS and time information.
        
        Returns:
            Formatted string containing OS information and current time.
            
        Example:
            >>> skill.run()
            'OS: Windows 10, Time: 2023-10-05 14:30:00'
        """
        os_info = f"{platform.system()} {platform.release()}"
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"OS: {os_info}, Time: {current_time}"


class SystemManagerFilesSkill(BMO_skill):
    """
    Skill to perform basic file operations.
    
    Supports creating, reading, writing, and deleting files with
    proper error handling and safety checks.
    """
    
    name: str = "system_manager_files"
    description: str = "Perform file operations (create, read, write, delete) on the system."
    args_schema: type[BaseModel] = SystemManagerFilesInput

    def _create_file(self, path: str) -> str:
        """
        Create a new file at specified path.
        
        Args:
            path: File path where the file should be created.
            
        Returns:
            Success message with file path.
            
        Raises:
            OSError: If file cannot be created due to permissions or invalid path.
        """
        file_path = Path(path)
        
        if file_path.exists():
            return f"Error: File already exists at {path}"
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("Created by BMO", encoding='utf-8')
            return f"File successfully created at {path}"
        except OSError as e:
            return f"Error creating file: {str(e)}"

    def _delete_file(self, path: str) -> str:
        """
        Delete file at specified path.
        
        Args:
            path: Path to file to be deleted.
            
        Returns:
            Success message or error description.
        """
        file_path = Path(path)
        
        if not file_path.exists():
            return f"Error: File not found at {path}"
        if not file_path.is_file():
            return f"Error: Path {path} is not a file"
            
        try:
            file_path.unlink()
            return f"File successfully deleted at {path}"
        except OSError as e:
            return f"Error deleting file: {str(e)}"

    def _read_file(self, path: str) -> str:
        """
        Read contents of file at specified path.
        
        Args:
            path: Path to file to be read.
            
        Returns:
            File contents or error message.
        """
        file_path = Path(path)
        
        if not file_path.exists():
            return f"Error: File not found at {path}"
        if not file_path.is_file():
            return f"Error: Path {path} is not a file"
            
        try:
            return file_path.read_text(encoding='utf-8')
        except OSError as e:
            return f"Error reading file: {str(e)}"

    def _write_file(self, path: str) -> str:
        """
        Write content to file at specified path.
        
        Args:
            path: Path to file to be written.
            
        Returns:
            Success message or error description.
        """
        file_path = Path(path)
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("Written by BMO", encoding='utf-8')
            return f"File successfully written at {path}"
        except OSError as e:
            return f"Error writing file: {str(e)}"

    def run(self, path: str = "", action: str = "create") -> str:
        """
        Execute requested file operation.
        
        Args:
            path: File path for the operation.
            action: Operation to perform (create, read, write, delete).
            
        Returns:
            Operation result or error message.
            
        Raises:
            ValidationError: If action is not one of the supported operations.
        """
        action_handlers: Dict[str, Any] = {
            "create": self._create_file,
            "delete": self._delete_file,
            "read": self._read_file,
            "write": self._write_file,
        }

        if action not in action_handlers:
            return f"Error: Invalid action '{action}'. Supported actions: {list(action_handlers.keys())}"

        if not path:
            return "Error: File path cannot be empty"

        handler = action_handlers[action]
        return handler(path)

# Auto-register skills with the registry
registry.register(SystemInfoSkill())
registry.register(SystemManagerFilesSkill())