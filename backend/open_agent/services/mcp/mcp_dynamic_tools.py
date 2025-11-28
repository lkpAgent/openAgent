"""Dynamic MCP tool wrapper for LangChain/LangGraph.

Fetches available MCP tools from the MCP server and exposes them as LangChain BaseTool
instances that call the MCP `/execute` endpoint at runtime.
"""
from typing import Any, Dict, List, Optional, Type
import json
import requests
from pydantic import BaseModel, Field, PrivateAttr
from langchain.tools import BaseTool

from open_agent.core.config import get_settings
from open_agent.utils.logger import get_logger
import os

logger = get_logger("mcp_dynamic_tools")

# Map MCP parameter types to Python type hints
_TYPE_MAP: Dict[str, Any] = {
    "string": str,
    "integer": int,
    "float": float,
    "boolean": bool,
    "array": List[Any],
    "object": Dict[str, Any],
}


def _build_args_schema(params: List[Dict[str, Any]]) -> Type[BaseModel]:
    """Build a Pydantic BaseModel class dynamically from MCP tool params."""
    annotations: Dict[str, Any] = {}
    fields: Dict[str, Any] = {}

    for p in params:
        name = p.get("name")
        ptype = p.get("type", "string")
        required = p.get("required", True)
        default = p.get("default", None)
        description = p.get("description", "")
        enum = p.get("enum")

        py_type = _TYPE_MAP.get(ptype, Any)
        annotations[name] = py_type

        if enum is not None and default is None:
            # if enum present without default, keep required unless specified
            field_default = ... if required else None
        else:
            field_default = ... if required and default is None else default

        fields[name] = Field(
            default=field_default,
            description=description,
        )

    # Create model class
    namespace = {"__annotations__": annotations}
    namespace.update(fields)
    return type("MCPToolArgs", (BaseModel,), namespace)


class MCPDynamicTool(BaseTool):
    """LangChain BaseTool wrapper that executes MCP tools via HTTP."""

    name: str
    description: str
    args_schema: Type[BaseModel]

    _mcp_base_url: str = PrivateAttr()
    _tool_name: str = PrivateAttr()

    def __init__(self, mcp_base_url: str, tool_info: Dict[str, Any]):
        # Initialize BaseTool with dynamic metadata
        super().__init__(
            name=tool_info.get("name", "tool"),
            description=tool_info.get("description", ""),
            args_schema=_build_args_schema(tool_info.get("parameters", [])),
        )
        # set private attrs after BaseTool init to avoid pydantic stripping
        self._mcp_base_url = mcp_base_url.rstrip("/")
        self._tool_name = tool_info["name"]

    def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self._mcp_base_url}/execute"
        payload = {
            "tool_name": self._tool_name,
            "parameters": params,
        }
        logger.info(f"调用 MCP 工具: {self._tool_name} 参数: {params}")
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data
        except Exception as e:
            logger.error(f"MCP 工具调用失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None,
                "tool_name": self._tool_name,
            }

    def _run(self, **kwargs: Any) -> str:
        """Synchronous execution for LangChain tools."""
        data = self._execute(kwargs)
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid MCP response"}, ensure_ascii=False)
        # Return string content; LangChain expects textual content for ToolMessage
        if data.get("success"):
            return json.dumps(data.get("result", {}), ensure_ascii=False)
        return json.dumps({"error": data.get("error")}, ensure_ascii=False)

    async def _arun(self, **kwargs: Any) -> str:
        # LangChain will call async version when available; we simply delegate to sync for now.
        return self._run(**kwargs)


def load_mcp_tools(include: Optional[List[str]] = None) -> List[MCPDynamicTool]:
    """Load MCP tools from the MCP server and construct dynamic tools.

    include: optional list of tool names to include (e.g., ["weather", "search"]).
    """
    settings = get_settings()
    # Try settings.tool.mcp_server_url, fallback to default
    mcp_base_url = getattr(settings.tool, "mcp_server_url", None) or os.getenv("MCP_SERVER_URL") or "http://127.0.0.1:8002"

    url = f"{mcp_base_url.rstrip('/')}/tools"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        tools_info = resp.json()
    except Exception as e:
        logger.error(f"获取 MCP 工具列表失败: {e}")
        return []

    dynamic_tools: List[MCPDynamicTool] = []
    for tool in tools_info:
        name = tool.get("name")
        if include and name not in include:
            continue
        try:
            dynamic_tools.append(MCPDynamicTool(mcp_base_url=mcp_base_url, tool_info=tool))
        except Exception as e:
            logger.warning(f"构建 MCP 工具'{name}'失败: {e}")
    logger.info(f"已加载 MCP 工具: {[t.name for t in dynamic_tools]}")
    return dynamic_tools