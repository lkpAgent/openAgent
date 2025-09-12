from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from typing import Optional, Type, ClassVar
import requests
import logging
from chat_agent.core.config import get_settings

logger = logging.getLogger("weather_tool")

# 定义输入参数模型（替代原get_parameters()）
class WeatherInput(BaseModel):
    location: str = Field(
        description="城市名称，例如：'北京'，只能是单个城市",
        examples=["北京", "上海", "New York"]
    )

class WeatherQueryTool(BaseTool):
    """心知天气API查询工具（LangChain标准版）"""
    name: ClassVar[str] = "天气API查询工具"
    description: ClassVar[str] = """通过心知天气API查询实时天气数据。 name = "天气API查询工具"  # 工具唯一标识 """
    args_schema: Type[BaseModel] = WeatherInput  # 参数规范
    # 使用PrivateAttr声明不参与验证的私有属性
    _api_key: str = PrivateAttr()
    _base_params: dict = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._api_key = get_settings().tool.weather_api_key
        if not self._api_key:
            raise ValueError("Weather API key not found in settings")

        # 基础请求参数
        self._base_params = {
            "key": self._api_key,
            "language": "zh-Hans",
            "unit": "c"
        }

    def _run(self, location: str) -> dict:
        """同步执行天气查询"""
        try:
            logger.info(f"查询天气 - 城市: {location}")

            # 构建API请求
            url = "https://api.seniverse.com/v3/weather/now.json"
            params = {**self._base_params, "location": location}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 处理API响应
            if 'results' not in data:
                error_msg = data.get('status', 'API返回格式异常')
                raise ValueError(f"天气API错误: {error_msg}")

            weather = data['results'][0]['now']
            return {
                "status": "success",
                "location": location,
                "temperature": weather["temperature"],
                "condition": weather["text"],
                "humidity": weather.get("humidity", "N/A"),
                "wind": weather.get("wind_direction", "N/A"),
                "full_data": weather
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求失败: {str(e)}")
            return {"status": "error", "message": f"网络错误: {str(e)}"}
        except Exception as e:
            logger.error(f"查询失败: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _arun(self, location: str) -> dict:
        """异步执行（示例实现）"""
        # 实际项目中可以用aiohttp替换requests
        return self._run(location)