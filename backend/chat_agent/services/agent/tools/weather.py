"""天气工具"""

from typing import List, Optional
from ..base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from ....core.config import get_settings
from ....utils.logger import get_logger

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
    """使用Tavily搜索引擎进行网络搜索的工具"""
    
    def __init__(self):
        """初始化搜索工具"""
        super().__init__()
        self.tavily_api_key = get_settings().llm.tavily_api_key
        self.  params = {
                "key": "SFU3cSAGMY_JHvpjJ",
                "location": loc,
                "language": "zh-Hans",
                "unit": "c",
            }
    
    def get_name(self) -> str:
        return "search"
    
    def get_description(self) -> str:
        return "使用Tavily搜索引擎进行网络搜索，可以搜索最新的信息"
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type=ToolParameterType.STRING,
                description="搜索查询内容",
                required=True
            ),
            ToolParameter(
                name="max_results",
                type=ToolParameterType.INTEGER,
                description="返回结果的最大数量（默认：5）",
                required=False,
                default=5
            ),
            ToolParameter(
                name="topic",
                type=ToolParameterType.STRING,
                description="搜索主题，可选值：general, academic, news, places",
                required=False,
                default="general"
            )
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行搜索"""
        try:
            query = kwargs.get("query")
            max_results = kwargs.get("max_results", 5)
            topic = kwargs.get("topic", "general")
            
            if not query:
                return ToolResult(
                    success=False,
                    error="搜索查询不能为空"
                )
            
            logger.info(f"执行网络搜索，查询：{query}")
            
            try:
                # 更新搜索参数
                self.search_tool.max_results = max_results
                self.search_tool.topic = topic
                
                # 执行搜索
                results = self.search_tool.invoke(query)
                
                # 格式化结果
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"{i}. **{result}**\n"
                    )
                
                result_text = "\n".join(formatted_results)
                
                logger.info(f"搜索完成，查询：{query}")
                
                return ToolResult(
                    success=True,
                    result={
                        "query": query,
                        "results": results,
                        "summary": f"找到 {len(results)} 个关于'{query}'的搜索结果：\n\n{result_text}"
                    }
                )
                
            except Exception as search_error:
                logger.warning(f"搜索失败：{str(search_error)}")
                return ToolResult(
                    success=False,
                    error=f"搜索执行失败：{str(search_error)}"
                )
            
        except Exception as e:
            logger.error(f"搜索错误：{str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"搜索失败：{str(e)}"
            )