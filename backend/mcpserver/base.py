"""Base classes for MCP server tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass
from enum import Enum

from .utils.logger import get_logger

logger = get_logger("tools")


class ToolParameterType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
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
    success: bool = Field(description="Whether the tool execution was successful")
    result: Any = Field(default=None, description="The result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class BaseTool(ABC):
    def __init__(self):
        self.name = self.get_name()
        self.description = self.get_description()
        self.parameters = self.get_parameters()
        
    @abstractmethod
    def get_name(self) -> str:
        pass
        
    @abstractmethod
    def get_description(self) -> str:
        pass
        
    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        pass
        
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass
        
    def get_schema(self) -> Dict[str, Any]:
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
        validated = {}
        for param in self.parameters:
            value = kwargs.get(param.name)
            if param.required and value is None:
                raise ValueError(f"Required parameter '{param.name}' is missing")
            if value is None and param.default is not None:
                value = param.default
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
                if param.enum and value not in param.enum:
                    raise ValueError(f"Parameter '{param.name}' must be one of {param.enum}")
            validated[param.name] = value
        return validated