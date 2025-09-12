"""天气工具"""

from typing import List, Optional
from chat_agent.services.agent.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from chat_agent.core.config import get_settings
from chat_agent.utils.logger import get_logger
import requests
logger = get_logger("weather_tool")
# @tool(args_schema=WeatherQuery)
# def get_weather(loc):
#     """
#         查询即时天气函数
#         :param loc: 必要参数，字符串类型，用于表示查询天气的具体城市名称，\
#         :return：心知天气 API查询即时天气的结果，具体URL请求地址为："https://api.seniverse.com/v3/weather/now.json"
#         返回结果对象类型为解析之后的JSON格式对象，并用字符串形式进行表示，其中包含了全部重要的天气信息
#     """
#     url = "https://api.seniverse.com/v3/weather/now.json"
#     params = {
#         "key": "SFU3cSAGMY_JHvpjJ",
#         "location": loc,
#         "language": "zh-Hans",
#         "unit": "c",
#     }
#     response = requests.get(url, params=params)
#     temperature = response.json()
#     return temperature['results'][0]['now']

class WeatherTool(BaseTool):
    """天气查询API"""
    
    def __init__(self):
        """初始化天气api工具"""
        super().__init__()
        self.weather_api_key = get_settings().tool.weather_api_key
        self.params = {
                "key": self.weather_api_key,
                "language": "zh-Hans",
                "unit": "c",
            }
    
    def get_name(self) -> str:
        return "weather"
    
    def get_description(self) -> str:
        return "使用天气api进行查找城市的天气情况"
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="loc",
                type=ToolParameterType.STRING,
                description="城市名称，如长沙",
                required=True
            )

        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """获取城市的天气情况"""
        try:
            # 支持两种参数名：loc 和 location
            loc = kwargs.get("loc") or kwargs.get("location")
            if not loc:
                return ToolResult(
                    success=False,
                    result="",
                    error="城市名称不能为空"
                )
            
            logger.info(f"查询城市天气信息，城市：{loc}")
            try:
                url = "https://api.seniverse.com/v3/weather/now.json"
                params = self.params.copy()
                params['location'] = loc
                response = requests.get(url, params=params)
                response.raise_for_status()  # 检查HTTP状态码
                
                temperature = response.json()
                
                # 检查API响应是否包含错误
                if 'results' not in temperature or not temperature['results']:
                    error_msg = temperature.get('message', '未知错误')
                    logger.warning(f"天气API返回错误：{error_msg}")
                    return ToolResult(
                        success=False,
                        result="",
                        error=f"天气API返回错误：{error_msg}"
                    )
                
                weather_data = temperature['results'][0]['now']
                logger.info(f"获取天气信息完成，查询：{weather_data}")
                return ToolResult(
                    success=True,
                    result={
                        "query": loc,
                        "results": weather_data,
                        "summary": f"找到 城市：'{loc}'的天气信息：\n\n{weather_data}"
                    }
                )
            except Exception as weather_error:
                logger.warning(f"获取天气信息失败：{str(weather_error)}")
                return ToolResult(
                    success=False,
                    result="",
                    error=f"获取天气信息失败：{str(weather_error)}"
                )
            
        except Exception as e:
            logger.error(f"获取天气信息失败：{str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                result="",
                error=f"获取天气信息失败：{str(e)}"
            )