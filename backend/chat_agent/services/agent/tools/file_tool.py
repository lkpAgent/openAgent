"""File tool for file operations."""

import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from ....utils.logger import get_logger

logger = get_logger("file_tool")


class FileTool(BaseTool):
    """Tool for file operations."""
    
    def get_name(self) -> str:
        return "file"
        
    def get_description(self) -> str:
        return "Read, write, and manage files. Supports text, JSON, and CSV files."
        
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="operation",
                type=ToolParameterType.STRING,
                description="File operation to perform",
                required=True,
                enum=["read", "write", "append", "list_dir", "file_info", "delete", "create_dir"]
            ),
            ToolParameter(
                name="file_path",
                type=ToolParameterType.STRING,
                description="Path to the file or directory",
                required=True
            ),
            ToolParameter(
                name="content",
                type=ToolParameterType.STRING,
                description="Content to write to file (for write/append operations)",
                required=False
            ),
            ToolParameter(
                name="file_type",
                type=ToolParameterType.STRING,
                description="File type for parsing",
                required=False,
                enum=["text", "json", "csv"],
                default="text"
            ),
            ToolParameter(
                name="encoding",
                type=ToolParameterType.STRING,
                description="File encoding",
                required=False,
                default="utf-8"
            ),
            ToolParameter(
                name="max_size",
                type=ToolParameterType.INTEGER,
                description="Maximum file size to read (in bytes)",
                required=False,
                default=1048576  # 1MB
            )
        ]
        
    def _is_safe_path(self, file_path: str) -> bool:
        """Check if the file path is safe to access."""
        try:
            # Convert to absolute path
            abs_path = os.path.abspath(file_path)
            
            # Define allowed directories (you can customize this)
            allowed_dirs = [
                os.path.abspath("./data"),
                os.path.abspath("./uploads"),
                os.path.abspath("./temp"),
                os.path.abspath("./output")
            ]
            
            # Check if path is within allowed directories
            for allowed_dir in allowed_dirs:
                if abs_path.startswith(allowed_dir):
                    return True
                    
            # For demo purposes, allow current directory and subdirectories
            current_dir = os.path.abspath(".")
            if abs_path.startswith(current_dir):
                return True
                
            return False
            
        except Exception:
            return False
            
    def _read_text_file(self, file_path: str, encoding: str, max_size: int) -> str:
        """Read text file."""
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            raise ValueError(f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)")
            
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
            
    def _read_json_file(self, file_path: str, encoding: str, max_size: int) -> Dict[str, Any]:
        """Read JSON file."""
        content = self._read_text_file(file_path, encoding, max_size)
        return json.loads(content)
        
    def _read_csv_file(self, file_path: str, encoding: str, max_size: int) -> List[Dict[str, Any]]:
        """Read CSV file."""
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            raise ValueError(f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)")
            
        rows = []
        with open(file_path, 'r', encoding=encoding, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
        return rows
        
    async def execute(self, operation: str, file_path: str, **kwargs) -> ToolResult:
        """Execute the file tool."""
        try:
            logger.info(f"Performing file operation: {operation} on {file_path}")
            
            # Security check
            if not self._is_safe_path(file_path):
                raise ValueError(f"Access to path '{file_path}' is not allowed for security reasons")
                
            if operation == "read":
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")
                    
                if not os.path.isfile(file_path):
                    raise ValueError(f"Path is not a file: {file_path}")
                    
                file_type = kwargs.get("file_type", "text")
                encoding = kwargs.get("encoding", "utf-8")
                max_size = kwargs.get("max_size", 1048576)
                
                if file_type == "json":
                    content = self._read_json_file(file_path, encoding, max_size)
                elif file_type == "csv":
                    content = self._read_csv_file(file_path, encoding, max_size)
                else:
                    content = self._read_text_file(file_path, encoding, max_size)
                    
                result = {
                    "file_path": file_path,
                    "file_type": file_type,
                    "content": content,
                    "size": os.path.getsize(file_path)
                }
                
                summary = f"Successfully read {file_type} file: {file_path} ({result['size']} bytes)"
                
            elif operation == "write":
                content = kwargs.get("content")
                if content is None:
                    raise ValueError("Content is required for write operation")
                    
                file_type = kwargs.get("file_type", "text")
                encoding = kwargs.get("encoding", "utf-8")
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                if file_type == "json":
                    # If content is string, try to parse it as JSON
                    if isinstance(content, str):
                        content = json.loads(content)
                    with open(file_path, 'w', encoding=encoding) as f:
                        json.dump(content, f, indent=2, ensure_ascii=False)
                else:
                    with open(file_path, 'w', encoding=encoding) as f:
                        f.write(str(content))
                        
                result = {
                    "file_path": file_path,
                    "file_type": file_type,
                    "bytes_written": os.path.getsize(file_path)
                }
                
                summary = f"Successfully wrote {file_type} file: {file_path} ({result['bytes_written']} bytes)"
                
            elif operation == "append":
                content = kwargs.get("content")
                if content is None:
                    raise ValueError("Content is required for append operation")
                    
                encoding = kwargs.get("encoding", "utf-8")
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'a', encoding=encoding) as f:
                    f.write(str(content))
                    
                result = {
                    "file_path": file_path,
                    "content_appended": len(str(content)),
                    "total_size": os.path.getsize(file_path)
                }
                
                summary = f"Successfully appended to file: {file_path} (total size: {result['total_size']} bytes)"
                
            elif operation == "list_dir":
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Directory not found: {file_path}")
                    
                if not os.path.isdir(file_path):
                    raise ValueError(f"Path is not a directory: {file_path}")
                    
                items = []
                for item in os.listdir(file_path):
                    item_path = os.path.join(file_path, item)
                    items.append({
                        "name": item,
                        "type": "directory" if os.path.isdir(item_path) else "file",
                        "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None,
                        "modified": os.path.getmtime(item_path)
                    })
                    
                result = {
                    "directory": file_path,
                    "items": items,
                    "total_items": len(items)
                }
                
                summary = f"Listed {len(items)} items in directory: {file_path}"
                
            elif operation == "file_info":
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Path not found: {file_path}")
                    
                stat = os.stat(file_path)
                result = {
                    "path": file_path,
                    "type": "directory" if os.path.isdir(file_path) else "file",
                    "size": stat.st_size,
                    "created": stat.st_ctime,
                    "modified": stat.st_mtime,
                    "accessed": stat.st_atime,
                    "permissions": oct(stat.st_mode)[-3:]
                }
                
                summary = f"File info for: {file_path} ({result['type']}, {result['size']} bytes)"
                
            elif operation == "delete":
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Path not found: {file_path}")
                    
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    result = {"deleted": file_path, "type": "file"}
                    summary = f"Successfully deleted file: {file_path}"
                else:
                    raise ValueError(f"Cannot delete directory with this operation: {file_path}")
                    
            elif operation == "create_dir":
                os.makedirs(file_path, exist_ok=True)
                result = {"created": file_path, "type": "directory"}
                summary = f"Successfully created directory: {file_path}"
                
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
            logger.info(f"File operation '{operation}' completed successfully")
            
            return ToolResult(
                success=True,
                result={
                    "summary": summary,
                    "details": result
                },
                metadata={
                    "operation": operation,
                    "file_path": file_path
                }
            )
            
        except Exception as e:
            logger.error(f"File tool error: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                result=None,
                error=f"File operation failed: {str(e)}"
            )