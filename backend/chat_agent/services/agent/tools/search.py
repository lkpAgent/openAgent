"""Search tool for web search functionality."""

import requests
from typing import Dict, Any, List
from ..base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from ....utils.logger import get_logger

logger = get_logger("search_tool")


class SearchTool(BaseTool):
    """Tool for performing web searches."""
    
    def get_name(self) -> str:
        return "search"
    
    def get_description(self) -> str:
        return "Search the web for information on a given topic"
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type=ToolParameterType.STRING,
                description="The search query to execute",
                required=True
            ),
            ToolParameter(
                name="num_results",
                type=ToolParameterType.INTEGER,
                description="Number of search results to return (default: 5)",
                required=False,
                default=5
            )
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute web search."""
        try:
            query = kwargs.get("query")
            num_results = kwargs.get("num_results", 5)
            
            if not query:
                return ToolResult(
                    success=False,
                    error="Search query is required"
                )
            
            logger.info(f"Performing web search for: {query}")
            
            # Use DuckDuckGo search for real web search
            try:
                import requests
                from urllib.parse import quote_plus
                
                # DuckDuckGo Instant Answer API
                search_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
                
                response = requests.get(search_url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                results = []
                
                # Extract abstract if available
                if data.get('Abstract'):
                    results.append({
                        "title": data.get('AbstractText', 'DuckDuckGo Abstract'),
                        "url": data.get('AbstractURL', ''),
                        "snippet": data.get('Abstract', '')
                    })
                
                # Extract related topics
                for topic in data.get('RelatedTopics', [])[:min(num_results-len(results), 4)]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        results.append({
                            "title": topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else topic.get('Text', ''),
                            "url": topic.get('FirstURL', ''),
                            "snippet": topic.get('Text', '')
                        })
                
                # If no results from DuckDuckGo, try a simple web search simulation
                if not results:
                    # Fallback to basic search results
                    results = [
                        {
                            "title": f"搜索结果：{query}",
                            "url": "https://www.google.com/search?q=" + quote_plus(query),
                            "snippet": f"关于'{query}'的搜索结果。建议您访问搜索引擎获取最新信息。"
                        }
                    ]
                
                # Format results for display
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"{i}. **{result['title']}**\n"
                        f"   URL: {result['url']}\n"
                        f"   {result['snippet']}\n"
                    )
                
                result_text = "\n".join(formatted_results)
                
                logger.info(f"Search completed successfully for query: {query}")
                
                return ToolResult(
                    success=True,
                    result={
                        "query": query,
                        "results": results,
                        "summary": f"找到 {len(results)} 个关于'{query}'的搜索结果:\n\n{result_text}"
                    }
                )
                
            except Exception as search_error:
                logger.warning(f"Web search failed, using fallback: {str(search_error)}")
                
                # Fallback to informative message
                fallback_result = {
                    "title": f"搜索：{query}",
                    "url": "https://www.google.com/search?q=" + quote_plus(query),
                    "snippet": f"无法获取'{query}'的实时搜索结果。建议您直接访问搜索引擎查询最新信息。"
                }
                
                return ToolResult(
                    success=True,
                    result={
                        "query": query,
                        "results": [fallback_result],
                        "summary": f"搜索'{query}':\n\n1. **{fallback_result['title']}**\n   URL: {fallback_result['url']}\n   {fallback_result['snippet']}"
                    }
                )
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )