"""
使用 LangChain 封装并调用本地 MCP 天气服务的示例与测试。
- 工具：调用 MCP `POST /execute`，执行 `weather`。
- 示例：查询长沙的天气，并打印结果。
- 测试：在设置了 WEATHER_API_KEY 时做成功断言；未设置时跳过成功测试。

运行方式：
1) 直接运行示例：
   python -m open_agent.tests.test_mcp_weather_langchain

2) 运行测试（需要 pytest）：
   pytest -q open_agent/tests/test_mcp_weather_langchain.py
"""
import os
import json
from typing import Optional, Dict, Any

import requests
from pydantic import BaseModel, Field

# LangChain 工具封装
try:
    from langchain.tools import StructuredTool  # 兼容 LangChain >=0.1.0
except Exception:
    # 旧版本兼容路径（如果需要）
    from langchain_core.tools import StructuredTool  # type: ignore


class WeatherInput(BaseModel):
    """天气查询入参 schema（LangChain StructuredTool 使用）。"""
    location: str = Field(..., description="城市名称，例如：北京/上海/长沙/New York")
    unit: Optional[str] = Field("c", description="温度单位（c 或 f），默认 c")
    language: Optional[str] = Field("zh-Hans", description="语言，默认 zh-Hans")


def mcp_weather_call(location: str, unit: str = "c", language: str = "zh-Hans") -> Dict[str, Any]:
    """调用本地 MCP 天气服务的包装函数。
    - 目标：POST /execute
    - Body：{"tool_name":"weather","parameters":{"location":...,"unit":...,"language":...}}
    返回：MCP服务的标准响应字典 {success, result, error, tool_name, executed_at}
    """
    base_url = os.getenv("MCP_BASE_URL", "http://127.0.0.1:8001")
    url = f"{base_url.rstrip('/')}/execute"
    payload = {
        "tool_name": "weather",
        "parameters": {
            "location": location,
            "unit": unit,
            "language": language,
        },
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"success": False, "error": f"HTTP error: {e}"}

    if not isinstance(data, dict):
        return {"success": False, "error": "Invalid response format", "raw": data}
    return data


weather_mcp_tool = StructuredTool.from_function(
    mcp_weather_call,
    name="weather_mcp",
    description="调用本地 MCP 天气服务查询城市实时天气。",
    args_schema=WeatherInput,
)


def pretty_print(title: str, obj: Any) -> None:
    print(f"\n=== {title} ===")
    try:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    except Exception:
        print(obj)


def _example_run() -> None:
    city = "北京"
    print(f"查询城市：{city}")



    result = weather_mcp_tool.invoke({
        "location": city,
        "unit": "c",
        "language": "zh-Hans",
    })
    pretty_print("MCP天气服务返回", result)


if __name__ == "__main__":
    _example_run()


# ------------------------
#         pytest
# ------------------------
import pytest


@pytest.mark.skipif(not os.getenv("WEATHER_API_KEY"), reason="未设置 WEATHER_API_KEY，跳过成功调用断言")
def test_mcp_weather_langchain_success():
    """在配置了 API Key 的情况下，调用应成功并返回规范化字段。"""
    res = weather_mcp_tool.invoke({
        "location": "长沙",
        "unit": "c",
        "language": "zh-Hans",
    })
    assert isinstance(res, dict)
    assert res.get("success") is True
    assert res.get("tool_name") == "weather"
    assert "result" in res

    # 规范化字段存在
    result = res["result"]
    assert isinstance(result, dict)
    assert result.get("location") is not None
    assert result.get("temperature") is not None
    assert result.get("text") is not None


def test_mcp_weather_langchain_without_key_handling():
    """未配置 API Key 时，工具返回错误信息；此用例仅验证错误处理，不要求成功。
    如果远端服务器已配置并返回成功，则跳过本测试。"""
    res = weather_mcp_tool.invoke({
        "location": "长沙",
        "unit": "c",
        "language": "zh-Hans",
    })
    # 如果服务端已配置密钥并返回成功，则跳过该用例
    if isinstance(res, dict) and res.get("success") is True:
        pytest.skip("服务器已配置 WEATHER_API_KEY，跳过无密钥错误处理测试")

    assert isinstance(res, dict)
    assert res.get("success") is False
    assert "error" in res