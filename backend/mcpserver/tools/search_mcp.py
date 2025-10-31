"""Search MCP (Model Context Protocol) tool using Tavily API.

Wraps the search functionality into the MCP tool pattern.
"""

import os
from typing import List, Dict, Any, Optional

try:
    import requests
except ImportError:
    requests = None
    import json
    from urllib import request as urllib_request

from mcpserver.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from mcpserver.utils.logger import get_logger

logger = get_logger("search_mcp_tool")


def _get_tavily_api_key() -> Optional[str]:
    # Read from environment only to avoid cross-config import side-effects
    return os.getenv("TAVILY_API_KEY")


class SearchMCPTool(BaseTool):
    """Web search MCP tool powered by Tavily API."""

    API_URL = "https://api.tavily.com/search"

    def get_name(self) -> str:
        return "search"

    def get_description(self) -> str:
        return "网络搜索MCP工具：使用Tavily搜索引擎获取最新信息与结果。"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type=ToolParameterType.STRING,
                description="搜索关键词或查询语句",
                required=True,
            ),
            ToolParameter(
                name="max_results",
                type=ToolParameterType.INTEGER,
                description="返回结果数量，默认5",
                required=False,
                default=5,
            ),
            ToolParameter(
                name="topic",
                type=ToolParameterType.STRING,
                description="搜索主题（如 general/news/coding 等，可选）",
                required=False,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        try:
            params = self.validate_parameters(**kwargs)
            api_key = _get_tavily_api_key()
            if not api_key:
                return ToolResult(success=False, error="Tavily API key not configured (set env TAVILY_API_KEY)")

            payload = {
                "api_key": api_key,
                "query": params["query"],
                "max_results": params.get("max_results", 5),
            }
            if params.get("topic"):
                payload["topic"] = params["topic"]

            if requests:
                try:
                    resp = requests.post(self.API_URL, json=payload, timeout=15)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error(f"Search API request failed: {e}")
                    return ToolResult(success=False, error=f"Search API request failed: {e}")
            else:
                try:
                    req = urllib_request.Request(self.API_URL, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                    with urllib_request.urlopen(req, timeout=15) as r:
                        body = r.read().decode("utf-8")
                        data = json.loads(body)
                except Exception as e:
                    logger.error(f"Search API request failed: {e}")
                    return ToolResult(success=False, error=f"Search API request failed: {e}")

            # Normalize result: return summary and results list
            normalized = {
                "query": params["query"],
                "summary": data.get("summary"),
                "results": data.get("results", []),
                "raw": data,
            }
            return ToolResult(success=True, result=normalized)
        except Exception as e:
            logger.error(f"Search tool execution error: {e}", exc_info=True)
            return ToolResult(success=False, error=str(e))