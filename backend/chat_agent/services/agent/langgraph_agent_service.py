"""LangGraph Agent service with tool calling capabilities."""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from .base import ToolRegistry
from chat_agent.services.tools import  WeatherQueryTool, TavilySearchTool, DateTimeTool
from ..postgresql_tool_manager import get_postgresql_tool
from ...core.config import get_settings
from ...utils.logger import get_logger
from ..agent_config import AgentConfigService

logger = get_logger("langgraph_agent_service")


class LangGraphAgentConfig(BaseModel):
    """LangGraph Agent configuration."""
    model_name: str = Field(default="gpt-3.5-turbo")
    model_provider: str = Field(default="openai")
    base_url: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)
    enabled_tools: List[str] = Field(default_factory=lambda: [
        "calculator", "weather", "search", "file", "image"
    ])
    max_iterations: int = Field(default=10)
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=1000)
    system_message: str = Field(
        default="""你是一个有用的AI助手，可以使用各种工具来帮助用户解决问题。
                重要规则：
                1. 工具调用失败时，必须仔细分析失败原因，特别是参数格式问题 
                3. 在重新调用工具前，先解释上次失败的原因和改进方案
                4. 确保每个工具调用的参数格式严格符合工具的要求 """
    )
    verbose: bool = Field(default=True)


class LangGraphAgentService:
    """LangGraph Agent service using create_react_agent."""
    
    def __init__(self, db_session=None):
        self.settings = get_settings()
        self.tool_registry = ToolRegistry()
        self.config = LangGraphAgentConfig()
        self.tools = []
        self.db_session = db_session
        self.config_service = AgentConfigService(db_session) if db_session else None
        self._initialize_tools()
        self._load_config()
        self._create_agent()
        
    def _initialize_tools(self):
        """Initialize available tools."""
        # Use the @tool decorated functions
        self.tools = [

            WeatherQueryTool(),
            TavilySearchTool(),
            DateTimeTool()
        ]
        

            
    def _load_config(self):
        """Load configuration from database if available."""
        if self.config_service:
            try:
                db_config = self.config_service.get_active_config()
                if db_config:
                    # Update config with database values
                    config_dict = db_config.config_data
                    for key, value in config_dict.items():
                        if hasattr(self.config, key):
                            setattr(self.config, key, value)
                    logger.info("Loaded configuration from database")
            except Exception as e:
                logger.warning(f"Failed to load config from database: {e}")
                

        
    def _create_agent(self):
        """Create LangGraph agent using create_react_agent."""
        try:
            # Initialize the model
            llm_config = get_settings().llm.get_current_config()
            self.model = init_chat_model(
                model=llm_config['model'],
                model_provider='openai',
                temperature=llm_config['temperature'],
                max_tokens=llm_config['max_tokens'],
                base_url= llm_config['base_url'],
                api_key=llm_config['api_key']
            )
            

            
            # Create the react agent
            self.agent = create_react_agent(
                model=self.model,
                tools=self.tools,)
            
            logger.info("LangGraph React agent created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create agent: {str(e)}")
            raise
        

            

            

        
    def _format_tools_info(self) -> str:
        """Format tools information for the prompt."""
        tools_info = []
        for tool_name in self.config.enabled_tools:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                params_info = []
                for param in tool.get_parameters():
                    params_info.append(f"  - {param.name} ({param.type.value}): {param.description}")
                
                tool_info = f"**{tool.get_name()}**: {tool.get_description()}"
                if params_info:
                    tool_info += "\n" + "\n".join(params_info)
                tools_info.append(tool_info)
                
        return "\n\n".join(tools_info)
        

        
    async def chat(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Process a chat message using LangGraph."""
        try:
            logger.info(f"Starting chat with message: {message[:100]}...")
            
            # Convert chat history to messages
            messages = []
            if chat_history:
                for msg in chat_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
                        
            # Add current message
            messages.append(HumanMessage(content=message))
            
            # Use the react agent directly
            result = await self.agent.ainvoke({"messages": messages}, {"recursion_limit": 6},)
            
            # Extract final response
            final_response = ""
            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    final_response = last_message.content
                elif isinstance(last_message, dict) and "content" in last_message:
                    final_response = last_message["content"]
                    
            return {
                "response": final_response,
                "intermediate_steps": [],
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"LangGraph chat error: {str(e)}", exc_info=True)
            return {
                "response": f"抱歉，处理您的请求时出现错误: {str(e)}",
                "intermediate_steps": [],
                "success": False,
                "error": str(e)
            }

    async def chat_stream(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> AsyncGenerator[
        Dict[str, Any], None]:
        """Process a chat message using LangGraph with streaming."""
        try:
            logger.info(f"Starting streaming chat with message: {message[:100]}...")

            # Convert chat history to messages
            messages = []
            if chat_history:
                for msg in chat_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

            # Add current message
            messages.append(HumanMessage(content=message))

            # Track state for streaming
            intermediate_steps = []
            final_response_started = False
            accumulated_response = ""
            final_ai_message = None

            # Stream the agent execution
            async for event in self.agent.astream({"messages": messages}):
                # Handle different event types from LangGraph
                print('event===', event)
                if isinstance(event, dict):
                    for node_name, node_output in event.items():
                        logger.info(f"Processing node: {node_name}, output type: {type(node_output)}")

                        # 处理 tools 节点
                        if "tools" in node_name.lower():
                            # 提取工具信息
                            tool_infos = []

                            if isinstance(node_output, dict) and "messages" in node_output:
                                messages_in_output = node_output["messages"]

                                for msg in messages_in_output:
                                    # 处理 ToolMessage 对象
                                    if hasattr(msg, 'name') and hasattr(msg, 'content'):
                                        tool_info = {
                                            "tool_name": msg.name,
                                            "tool_output": msg.content,
                                            "tool_call_id": getattr(msg, 'tool_call_id', ''),
                                            "status": "completed"
                                        }
                                        tool_infos.append(tool_info)
                                    elif isinstance(msg, dict):
                                        if 'name' in msg and 'content' in msg:
                                            tool_info = {
                                                "tool_name": msg['name'],
                                                "tool_output": msg['content'],
                                                "tool_call_id": msg.get('tool_call_id', ''),
                                                "status": "completed"
                                            }
                                            tool_infos.append(tool_info)

                            # 返回 tools_end 事件
                            for tool_info in tool_infos:
                                yield {
                                    "type": "tools_end",
                                    "content": f"工具 {tool_info['tool_name']} 执行完成",
                                    "tool_name": tool_info["tool_name"],
                                    "tool_output": tool_info["tool_output"],
                                    "node_name": node_name,
                                    "done": False
                                }
                                await asyncio.sleep(0.1)

                        # 处理 agent 节点
                        elif "agent" in node_name.lower():
                            if isinstance(node_output, dict) and "messages" in node_output:
                                messages_in_output = node_output["messages"]
                                if messages_in_output:
                                    last_msg = messages_in_output[-1]

                                    # 获取 finish_reason
                                    finish_reason = None
                                    if hasattr(last_msg, 'response_metadata'):
                                        finish_reason = last_msg.response_metadata.get('finish_reason')
                                    elif isinstance(last_msg, dict) and 'response_metadata' in last_msg:
                                        finish_reason = last_msg['response_metadata'].get('finish_reason')

                                    # 判断是否为 thinking 或 response
                                    if finish_reason == 'tool_calls':
                                        # thinking 状态
                                        thinking_content = "🤔 正在思考..."
                                        if hasattr(last_msg, 'content') and last_msg.content:
                                            thinking_content = f"🤔 思考: {last_msg.content[:200]}..."
                                        elif isinstance(last_msg, dict) and "content" in last_msg:
                                            thinking_content = f"🤔 思考: {last_msg['content'][:200]}..."

                                        yield {
                                            "type": "thinking",
                                            "content": thinking_content,
                                            "node_name": node_name,
                                            "raw_output": str(node_output)[:500] if node_output else "",
                                            "done": False
                                        }
                                        await asyncio.sleep(0.1)

                                    elif finish_reason == 'stop':
                                        # response 状态
                                        if hasattr(last_msg, 'content') and hasattr(last_msg,
                                                                                    '__class__') and 'AI' in last_msg.__class__.__name__:
                                            current_content = last_msg.content
                                            final_ai_message = last_msg

                                            if not final_response_started and current_content:
                                                final_response_started = True
                                                yield {
                                                    "type": "response_start",
                                                    "content": "",
                                                    "intermediate_steps": intermediate_steps,
                                                    "done": False
                                                }

                                            if current_content and len(current_content) > len(accumulated_response):
                                                new_content = current_content[len(accumulated_response):]

                                                for char in new_content:
                                                    accumulated_response += char
                                                    yield {
                                                        "type": "response",
                                                        "content": accumulated_response,
                                                        "intermediate_steps": intermediate_steps,
                                                        "done": False
                                                    }
                                                    await asyncio.sleep(0.03)

                                    else:
                                        # 其他 agent 状态
                                        yield {
                                            "type": "step",
                                            "content": f"📋 执行步骤: {node_name}",
                                            "node_name": node_name,
                                            "raw_output": str(node_output)[:500] if node_output else "",
                                            "done": False
                                        }
                                        await asyncio.sleep(0.1)

                        # 处理其他节点
                        else:
                            yield {
                                "type": "step",
                                "content": f"📋 执行步骤: {node_name}",
                                "node_name": node_name,
                                "raw_output": str(node_output)[:500] if node_output else "",
                                "done": False
                            }
                            await asyncio.sleep(0.1)

            # 最终完成事件
            yield {
                "type": "complete",
                "content": accumulated_response,
                "intermediate_steps": intermediate_steps,
                "done": True
            }

        except Exception as e:
            logger.error(f"Error in chat_stream: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "content": f"处理请求时出错: {str(e)}",
                "done": True
            }
                                        
            # 确保最终响应包含完整内容
            final_content = accumulated_response
            if not final_content and final_ai_message and hasattr(final_ai_message, 'content'):
                final_content = final_ai_message.content or ""
            
            # Final completion signal
            yield {
                "type": "response",
                "content": final_content,
                "intermediate_steps": intermediate_steps,
                "done": True
            }
            
        except Exception as e:
            logger.error(f"LangGraph chat stream error: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "content": f"抱歉，处理您的请求时出现错误: {str(e)}",
                "error": str(e),
                "done": True
            }
            
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        tools = []
        for tool in self.tools:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": [],
                "enabled": True
            })
        return tools
        
    def get_config(self) -> Dict[str, Any]:
        """Get current agent configuration."""
        return self.config.dict()
        
    def update_config(self, config: Dict[str, Any]):
        """Update agent configuration."""
        for key, value in config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Recreate agent with new config
        self._create_agent()
        logger.info("Agent configuration updated")


# Global instance
_langgraph_agent_service: Optional[LangGraphAgentService] = None


def get_langgraph_agent_service(db_session=None) -> LangGraphAgentService:
    """Get or create LangGraph agent service instance."""
    global _langgraph_agent_service
    
    if _langgraph_agent_service is None:
        _langgraph_agent_service = LangGraphAgentService(db_session)
        logger.info("LangGraph Agent service initialized")
        
    return _langgraph_agent_service