"""基于TavilySearch的搜索工具"""

from typing import List, Optional
# from langchain_community.tools import TavilySearch
from langchain_tavily import TavilySearch


from ..base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from ....core.config import get_settings
from ....utils.logger import get_logger

logger = get_logger("search_tool")


class SearchTool(BaseTool):
    """使用Tavily搜索引擎进行网络搜索的工具"""
    
    def __init__(self):
        """初始化搜索工具"""
        super().__init__()
        self.tavily_api_key = get_settings().tool.tavily_api_key
        if not self.tavily_api_key:
            raise ValueError("Tavily API key not found in settings")
        self.search_tool = TavilySearch(
            max_results=5,
            topic="general",
            tavily_api_key=self.tavily_api_key
        )
    
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
    
    def execute(self, params: dict) -> ToolResult:
        """执行搜索"""
        try:
            query = params.get("query")
            max_results = params.get("max_results", 5)
            topic = params.get("topic", "general")
            
            if not query:
                return ToolResult(
                    success=False,
                    result=None,
                    error="搜索查询不能为空"
                )
            
            logger.info(f"执行网络搜索，查询：{query}")
            
            try:
                # 更新搜索参数
                self.search_tool.max_results = max_results
                self.search_tool.topic = topic
                
                # 执行搜索
                try:
                    results = self.search_tool.invoke(query)
                    
                    # 检查结果是否包含错误信息
                    if isinstance(results, dict) and 'error' in results:
                        error_msg = str(results['error'])
                        if 'Unauthorized' in error_msg:
                            error_msg = "Tavily API密钥无效或未授权"
                        logger.warning(f"搜索失败：{error_msg}")
                        return ToolResult(
                            success=False,
                            result=None,
                            error=error_msg
                        )
                    
                    # 格式化结果
                    formatted_results = []
                    if isinstance(results, list):
                        for result in results:
                            if isinstance(result, dict):
                                formatted_result = {
                                    "title": result.get('title', ''),
                                    "url": result.get('url', ''),
                                    "content": result.get('content', '')
                                }
                            else:
                                formatted_result = {
                                    "title": str(result),
                                    "url": "",
                                    "content": ""
                                }
                            formatted_results.append(formatted_result)
                    else:
                        formatted_results = [{
                            "title": str(results),
                            "url": "",
                            "content": ""
                        }]
                    
                    logger.info(f"搜索完成，查询：{query}")
                    
                    return ToolResult(
                        success=True,
                        result=formatted_results
                    )
                    
                except Exception as e:
                    error_msg = str(e)
                    if 'Unauthorized' in error_msg:
                        error_msg = "Tavily API密钥无效或未授权"
                    logger.warning(f"搜索失败：{error_msg}")
                    return ToolResult(
                        success=False,
                        result=None,
                        error=error_msg
                    )
                
            except Exception as search_error:
                logger.warning(f"搜索失败：{str(search_error)}")
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"搜索执行失败：{str(search_error)}"
                )
            
        except Exception as e:
            logger.error(f"搜索错误：{str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                result=None,
                error=f"搜索失败：{str(e)}"
            )