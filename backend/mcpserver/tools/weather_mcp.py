"""
Weather MCP (Model Context Protocol) tool for querying real-time weather.

This wraps the existing weather functionality into the MCP tool pattern.
"""

import os
from typing import List, Dict, Any, Optional

try:
    import requests  # Prefer requests if available
except ImportError:
    requests = None
    import json
    from urllib import request as urllib_request, parse as urllib_parse

from mcpserver.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from mcpserver.utils.logger import get_logger

logger = get_logger("weather_mcp_tool")


# Helper to obtain API key from environment only (avoid cross-config import issues)
def _get_weather_api_key() -> Optional[str]:
    key = os.getenv("WEATHER_API_KEY")
    if not key:
        logger.warning("WEATHER_API_KEY 未在进程环境中找到，请确认已加载 .env 或设置系统环境变量")
    else:
        logger.info("WEATHER_API_KEY 已从进程环境变量加载")
    return key


class WeatherMCPTool(BaseTool):
    """Weather MCP tool using Seniverse (心知天气) API."""

    BASE_URL = "https://api.seniverse.com/v3/weather/now.json"

    def get_name(self) -> str:
        return "weather"

    def get_description(self) -> str:
        return "天气查询MCP工具：根据城市名称查询当前实时天气（基于心知天气API）。"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="location",
                type=ToolParameterType.STRING,
                description="城市名称，例如：北京/上海/New York，仅支持单个城市",
                required=True,
            ),
            ToolParameter(
                name="language",
                type=ToolParameterType.STRING,
                description="语言（默认 zh-Hans）",
                required=False,
                default="zh-Hans",
            ),
            ToolParameter(
                name="unit",
                type=ToolParameterType.STRING,
                description="温度单位（c 或 f，默认 c）",
                required=False,
                default="c",
                enum=["c", "f"],
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """Execute weather query."""
        try:
            params = self.validate_parameters(**kwargs)
            logger.info(f"Weather params received: location={params.get('location')!r}, language={params.get('language')!r}, unit={params.get('unit')!r}")
            api_key = _get_weather_api_key()
            if not api_key:
                return ToolResult(success=False, error="Weather API key not configured (set env WEATHER_API_KEY)")

            # Ensure location is a str and preserve unicode
            location_val = params.get("location")
            if isinstance(location_val, bytes):
                try:
                    location_val = location_val.decode("utf-8")
                except Exception:
                    location_val = location_val.decode(errors="ignore")
            if not isinstance(location_val, str):
                location_val = str(location_val)
            logger.info(f"Normalized location value: {location_val!r}")

            query_params = {
                "key": api_key,
                "location": location_val,
                "language": params.get("language", "zh-Hans"),
                "unit": params.get("unit", "c"),
            }
            logger.info(f"Query params prepared: {query_params}")

            # Perform HTTP request
            if requests:
                try:
                    resp = requests.get(self.BASE_URL, params=query_params, timeout=10)
                    logger.info(f"Weather API full URL: {resp.request.url}")
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error(f"Weather API request failed: {e}")
                    return ToolResult(success=False, error=f"Weather API request failed: {e}")
            else:
                # Fallback to urllib
                try:
                    url = f"{self.BASE_URL}?" + urllib_parse.urlencode(query_params, encoding="utf-8")
                    logger.info(f"Weather API full URL (urllib): {url}")
                    with urllib_request.urlopen(url, timeout=10) as r:
                        body = r.read().decode("utf-8")
                        data = json.loads(body)
                except Exception as e:
                    logger.error(f"Weather API request failed: {e}")
                    return ToolResult(success=False, error=f"Weather API request failed: {e}")

            # Normalize result
            try:
                results = data.get("results") or []
                now = results[0]["now"] if results else {}
                location_info = results[0]["location"] if results else {}
                normalized = {
                    "location": location_info.get("name") or params["location"],
                    "text": now.get("text"),
                    "temperature": now.get("temperature"),
                    "humidity": now.get("humidity"),
                    "wind_direction": now.get("wind_direction"),
                    "wind_speed": now.get("wind_speed"),
                    "last_update": now.get("last_update"),
                    "raw": data,
                }
                return ToolResult(success=True, result=normalized)
            except Exception:
                # If structure differs, return raw
                return ToolResult(success=True, result=data)
        except Exception as e:
            logger.error(f"Weather tool execution error: {e}", exc_info=True)
            return ToolResult(success=False, error=str(e))