"""基于TavilySearch的搜索工具"""

from open_agent.core.config import get_settings
from open_agent.utils.logger import get_logger

logger = get_logger("search_tool")

from langchain.tools import BaseTool
from langchain_community.tools.tavily_search import TavilySearchResults
from pydantic import BaseModel, Field, PrivateAttr
from typing import Optional, Type, ClassVar
import logging

logger = logging.getLogger(__name__)


# 定义输入参数模型（替代原get_parameters()）
class SearchInput(BaseModel):
    query: str = Field(description="搜索查询内容")
    max_results: Optional[int] = Field(
        default=5,
        description="返回结果的最大数量（默认：5）"
    )
    topic: Optional[str] = Field(
        default="general",
        description="搜索主题，可选值：general, academic, news, places"
    )


class TavilySearchTool(BaseTool):
    name:ClassVar[str] = "tavily_search_tool"
    description:ClassVar[str]  = """使用Tavily搜索引擎进行网络搜索，可以获取最新信息。
    输入应该包含搜索查询(query)，可选参数包括max_results和topic。"""  # 替代get_description()
    args_schema: Type[BaseModel] = SearchInput  # 用Pydantic模型定义参数
    _tavily_api_key: str = PrivateAttr()
    _search_client: TavilySearchResults = PrivateAttr()
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tavily_api_key = get_settings().tool.tavily_api_key
        if not self._tavily_api_key:
            raise ValueError("Tavily API key not found in settings")

        # 初始化Tavily客户端
        self._search_client = TavilySearchResults(
            tavily_api_key=self._tavily_api_key
        )

    def _run(self, query: str, max_results: int = 5, topic: str = "general"):
        try:
            logger.info(f"执行搜索：{query}")
            # 调用Tavily（LangChain已内置Tavily工具，这里直接使用）
            results = self._search_client.run({
                "query": query,
                "max_results": max_results,
                "topic": topic
            })

            # 格式化结果（根据Tavily的实际返回结构调整）
            if isinstance(results, list):
                return {
                    "status": "success",
                    "results": [
                        {
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "content": r.get("content", "")[:200] + "..."
                        } for r in results
                    ]
                }
            else:
                return {"status": "error", "message": "Unexpected result format"}

        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _arun(self, **kwargs):
        """异步版本"""
        """直接调用同步版本"""
        return self._run(**kwargs)  # 直接委托给同步方法