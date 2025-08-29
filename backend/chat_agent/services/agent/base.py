"""Base classes for Agent tools."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Callable
from pydantic import BaseModel, Field
from dataclasses import dataclass
from enum import Enum

from ...utils.logger import get_logger

logger = get_logger("agent_tools")


class ToolParameterType(str, Enum):
    """Tool parameter types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON schema."""
        param_dict = {
            "type": self.type.value,
            "description": self.description
        }
        
        if self.enum:
            param_dict["enum"] = self.enum
            
        if self.default is not None:
            param_dict["default"] = self.default
            
        return param_dict


class ToolResult(BaseModel):
    """Tool execution result."""
    success: bool = Field(description="Whether the tool execution was successful")
    result: Any = Field(description="The result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class BaseTool(ABC):
    """Base class for all Agent tools."""
    
    def __init__(self):
        self.name = self.get_name()
        self.description = self.get_description()
        self.parameters = self.get_parameters()
        
    @abstractmethod
    def get_name(self) -> str:
        """Get tool name."""
        pass
        
    @abstractmethod
    def get_description(self) -> str:
        """Get tool description."""
        pass
        
    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """Get tool parameters."""
        pass
        
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
        
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LangChain."""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = param.to_dict()
            if param.required:
                required.append(param.name)
                
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
        
    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Validate and process input parameters."""
        validated = {}
        
        for param in self.parameters:
            value = kwargs.get(param.name)
            
            # Check required parameters
            if param.required and value is None:
                raise ValueError(f"Required parameter '{param.name}' is missing")
                
            # Use default if not provided
            if value is None and param.default is not None:
                value = param.default
                
            # Type validation (basic)
            if value is not None:
                if param.type == ToolParameterType.INTEGER and not isinstance(value, int):
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        raise ValueError(f"Parameter '{param.name}' must be an integer")
                        
                elif param.type == ToolParameterType.FLOAT and not isinstance(value, (int, float)):
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        raise ValueError(f"Parameter '{param.name}' must be a number")
                        
                elif param.type == ToolParameterType.BOOLEAN and not isinstance(value, bool):
                    if isinstance(value, str):
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        value = bool(value)
                        
                # Enum validation
                if param.enum and value not in param.enum:
                    raise ValueError(f"Parameter '{param.name}' must be one of {param.enum}")
                    
            validated[param.name] = value
            
        return validated


class ToolRegistry:
    """Registry for managing Agent tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._enabled_tools: Dict[str, bool] = {}
        
    def register(self, tool: BaseTool, enabled: bool = True) -> None:
        """Register a tool."""
        tool_name = tool.get_name()
        self._tools[tool_name] = tool
        self._enabled_tools[tool_name] = enabled
        logger.info(f"Registered tool: {tool_name} (enabled: {enabled})")
        
    def unregister(self, tool_name: str) -> None:
        """Unregister a tool."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            del self._enabled_tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
            
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(tool_name)
        
    def get_enabled_tools(self) -> Dict[str, BaseTool]:
        """Get all enabled tools."""
        return {
            name: tool for name, tool in self._tools.items()
            if self._enabled_tools.get(name, False)
        }
        
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tools."""
        return self._tools.copy()
        
    def enable_tool(self, tool_name: str) -> None:
        """Enable a tool."""
        if tool_name in self._tools:
            self._enabled_tools[tool_name] = True
            logger.info(f"Enabled tool: {tool_name}")
            
    def disable_tool(self, tool_name: str) -> None:
        """Disable a tool."""
        if tool_name in self._tools:
            self._enabled_tools[tool_name] = False
            logger.info(f"Disabled tool: {tool_name}")
            
    def is_enabled(self, tool_name: str) -> bool:
        """Check if a tool is enabled."""
        return self._enabled_tools.get(tool_name, False)
        
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get schema for all enabled tools."""
        enabled_tools = self.get_enabled_tools()
        return [tool.get_schema() for tool in enabled_tools.values()]
        
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool with given parameters."""
        tool = self.get_tool(tool_name)
        
        if not tool:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool '{tool_name}' not found"
            )
            
        if not self.is_enabled(tool_name):
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool '{tool_name}' is disabled"
            )
            
        try:
            # Validate parameters
            validated_params = tool.validate_parameters(**kwargs)
            
            # Execute tool
            result = await tool.execute(**validated_params)
            logger.info(f"Tool '{tool_name}' executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution failed: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool execution failed: {str(e)}"
            )


# Global tool registry instance
tool_registry = ToolRegistry()