"""LangChain Agent service with tool calling capabilities."""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain.agents import AgentExecutor, create_openai_tools_agent,create_tool_calling_agent
from langchain.tools import BaseTool as LangChainBaseTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .base import BaseTool, ToolRegistry, ToolResult
from .tools import CalculatorTool, WeatherTool, SearchTool, DateTimeTool, FileTool, GenerateImageTool
from ..postgresql_tool_manager import get_postgresql_tool
from ...core.config import get_settings
from ...utils.logger import get_logger
from ..agent_config import AgentConfigService

logger = get_logger("agent_service")


class LangChainToolWrapper(LangChainBaseTool):
    """Wrapper to convert our BaseTool to LangChain tool."""
    
    name: str = Field(...)
    description: str = Field(...)
    base_tool: BaseTool = Field(...)
    
    def __init__(self, base_tool: BaseTool, **kwargs):
        super().__init__(
            name=base_tool.get_name(),
            description=base_tool.get_description(),
            base_tool=base_tool,
            **kwargs
        )
    
    def _run(self, *args, **kwargs) -> str:
        """Synchronous run method."""
        # Handle both positional and keyword arguments
        if args:
            # If positional arguments are provided, convert them to kwargs
            # based on the tool's parameter names
            params = self.base_tool.get_parameters()
            for i, arg in enumerate(args):
                if i < len(params):
                    kwargs[params[i].name] = arg
        
        # Run async method in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.base_tool.execute(**kwargs))
            return self._format_result(result)
        finally:
            loop.close()
    
    async def _arun(self, *args, **kwargs) -> str:
        """Asynchronous run method."""
        # Handle both positional and keyword arguments
        if args:
            # If positional arguments are provided, convert them to kwargs
            # based on the tool's parameter names
            params = self.base_tool.get_parameters()
            for i, arg in enumerate(args):
                if i < len(params):
                    kwargs[params[i].name] = arg
        
        result = await self.base_tool.execute(**kwargs)
        return self._format_result(result)
    
    def _format_result(self, result: ToolResult) -> str:
        """Format tool result for LangChain."""
        if result.success:
            if isinstance(result.result, dict) and "summary" in result.result:
                return result.result["summary"]
            return str(result.result)
        else:
            return f"Error: {result.error}"


class AgentConfig(BaseModel):
    """Agent configuration."""
    enabled_tools: List[str] = Field(default_factory=lambda: [
        "calculator", "weather", "search", "datetime", "file", "generate_image", "postgresql_mcp"
    ])
    max_iterations: int = Field(default=10)
    temperature: float = Field(default=0.1)
    system_message: str = Field(
        default="You are a helpful AI assistant with access to various tools. "
                "Use the available tools to help answer user questions accurately. "
                "Always explain your reasoning and the tools you're using."
    )
    verbose: bool = Field(default=True)


class AgentService:
    """LangChain Agent service with tool calling capabilities."""
    
    def __init__(self, db_session=None):
        self.settings = get_settings()
        self.tool_registry = ToolRegistry()
        self.config = AgentConfig()
        self.agent_executor: Optional[AgentExecutor] = None
        self.db_session = db_session
        self.config_service = AgentConfigService(db_session) if db_session else None
        self._initialize_tools()
        self._load_config()
        
    def _initialize_tools(self):
        """Initialize and register all available tools."""
        tools = [
            CalculatorTool(),
            WeatherTool(),
            SearchTool(),
            DateTimeTool(),
            FileTool(),
            GenerateImageTool(),
            get_postgresql_tool()  # 使用单例PostgreSQL MCP工具
        ]
        
        for tool in tools:
            self.tool_registry.register(tool)
            logger.info(f"Registered tool: {tool.get_name()}")
    
    def _load_config(self):
        """Load configuration from database if available."""
        if self.config_service:
            try:
                config_dict = self.config_service.get_config_dict()
                # Update config with database values
                for key, value in config_dict.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                logger.info("Loaded agent configuration from database")
            except Exception as e:
                logger.warning(f"Failed to load config from database, using defaults: {str(e)}")

    def _get_enabled_tools(self) -> List[LangChainToolWrapper]:
        """Get list of enabled LangChain tools."""
        enabled_tools = []
        
        for tool_name in self.config.enabled_tools:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                langchain_tool = LangChainToolWrapper(base_tool=tool)
                enabled_tools.append(langchain_tool)
                logger.debug(f"Enabled tool: {tool_name}")
            else:
                logger.warning(f"Tool not found: {tool_name}")
                
        return enabled_tools
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Create LangChain agent executor."""
        # Get LLM configuration
        llm_config = self.settings.llm.get_current_config()
        
        # Create LLM instance
        llm = ChatOpenAI(
            model=llm_config["model"],
            api_key=llm_config["api_key"],
            base_url=llm_config["base_url"],
            temperature=self.config.temperature,
            max_tokens=self.settings.llm.max_tokens
        )
        
        # Get enabled tools
        tools = self._get_enabled_tools()
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config.system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        agent = create_tool_calling_agent(llm, tools, prompt)
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            max_iterations=self.config.max_iterations,
            verbose=self.config.verbose,
            return_intermediate_steps=True
        )
        
        return agent_executor
    
    async def chat(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Process chat message with agent."""
        try:
            logger.info(f"Processing agent chat message: {message[:100]}...")
            
            # Create agent executor if not exists
            if not self.agent_executor:
                self.agent_executor = self._create_agent_executor()
            
            # Convert chat history to LangChain format
            langchain_history = []
            if chat_history:
                for msg in chat_history:
                    if msg["role"] == "user":
                        langchain_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        langchain_history.append(AIMessage(content=msg["content"]))
            
            # Execute agent
            result = await self.agent_executor.ainvoke({
                "input": message,
                "chat_history": langchain_history
            })
            
            # Extract response and intermediate steps
            response = result["output"]
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Format tool calls for response
            tool_calls = []
            for step in intermediate_steps:
                if len(step) >= 2:
                    action, observation = step[0], step[1]
                    tool_calls.append({
                        "tool": action.tool,
                        "input": action.tool_input,
                        "output": observation
                    })
            
            logger.info(f"Agent response generated successfully with {len(tool_calls)} tool calls")
            
            return {
                "response": response,
                "tool_calls": tool_calls,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Agent chat error: {str(e)}", exc_info=True)
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "tool_calls": [],
                "success": False,
                "error": str(e)
            }
    
    async def chat_stream(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Process chat message with agent (streaming)."""
        tool_calls = []  # Initialize tool_calls at the beginning
        try:
            logger.info(f"Processing agent chat stream: {message[:100]}...")
            
            # Create agent executor if not exists
            if not self.agent_executor:
                self.agent_executor = self._create_agent_executor()
            
            # Convert chat history to LangChain format
            langchain_history = []
            if chat_history:
                for msg in chat_history:
                    if msg["role"] == "user":
                        langchain_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        langchain_history.append(AIMessage(content=msg["content"]))
            
            # Yield initial status
            yield {
                "type": "status",
                "content": "🤖 开始分析您的请求...",
                "done": False
            }
            await asyncio.sleep(0.2)
            
            # Use astream_events for real streaming (if available) or fallback to simulation
            try:
                # Try to use streaming events if available
                async for event in self.agent_executor.astream_events(
                    {"input": message, "chat_history": langchain_history},
                    version="v1"
                ):
                    if event["event"] == "on_tool_start":
                        tool_name = event["name"]
                        yield {
                            "type": "tool_start",
                            "content": f"🔧 正在使用工具: {tool_name}",
                            "tool_name": tool_name,
                            "done": False
                        }
                        await asyncio.sleep(0.1)
                    
                    elif event["event"] == "on_tool_end":
                        tool_name = event["name"]
                        yield {
                            "type": "tool_end",
                            "content": f"✅ 工具 {tool_name} 执行完成",
                            "tool_name": tool_name,
                            "done": False
                        }
                        await asyncio.sleep(0.1)
                    
                    elif event["event"] == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        if hasattr(chunk, 'content') and chunk.content:
                            yield {
                                "type": "content",
                                "content": chunk.content,
                                "done": False
                            }
                            await asyncio.sleep(0.05)
                            
            except Exception as stream_error:
                logger.warning(f"Streaming events not available, falling back to simulation: {stream_error}")
                
                # Fallback: Execute agent and simulate streaming
                result = await self.agent_executor.ainvoke({
                    "input": message,
                    "chat_history": langchain_history
                })
                
                # Extract response and intermediate steps
                response = result["output"]
                intermediate_steps = result.get("intermediate_steps", [])
                
                # Yield tool execution steps
                tool_calls = []
                for i, step in enumerate(intermediate_steps):
                    if len(step) >= 2:
                        action, observation = step[0], step[1]
                        tool_calls.append({
                            "tool": action.tool,
                            "input": action.tool_input,
                            "output": observation
                        })
                        
                        # Yield tool execution status
                        yield {
                            "type": "tool",
                            "content": f"🔧 使用工具 {action.tool}: {str(action.tool_input)[:100]}...",
                            "tool_name": action.tool,
                            "tool_input": action.tool_input,
                            "done": False
                        }
                        await asyncio.sleep(0.3)
                        
                        yield {
                            "type": "tool_result",
                            "content": f"✅ 工具结果: {str(observation)[:200]}...",
                            "tool_name": action.tool,
                            "done": False
                        }
                        await asyncio.sleep(0.2)
                
                # Yield thinking status
                yield {
                    "type": "thinking",
                    "content": "🤔 正在整理回答...",
                    "done": False
                }
                await asyncio.sleep(0.3)
                
                # Yield the final response in chunks to simulate streaming
                words = response.split()
                current_content = ""
                
                for i, word in enumerate(words):
                    current_content += word + " "
                    
                    # Yield every 2-3 words or at the end
                    if (i + 1) % 2 == 0 or i == len(words) - 1:
                        yield {
                            "type": "response",
                            "content": current_content.strip(),
                            "tool_calls": tool_calls if i == len(words) - 1 else [],
                            "done": i == len(words) - 1
                        }
                        
                        # Small delay to simulate typing
                        if i < len(words) - 1:
                            await asyncio.sleep(0.05)
            
            logger.info(f"Agent stream response completed with {len(tool_calls)} tool calls")
            
        except Exception as e:
            logger.error(f"Agent chat stream error: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "content": f"Sorry, I encountered an error: {str(e)}",
                "done": True
            }
    
    def update_config(self, config: Dict[str, Any]):
        """Update agent configuration."""
        try:
            # Update configuration
            for key, value in config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    logger.info(f"Updated agent config: {key} = {value}")
            
            # Reset agent executor to apply new config
            self.agent_executor = None
            
        except Exception as e:
            logger.error(f"Error updating agent config: {str(e)}", exc_info=True)
            raise
    
    def load_config_from_db(self, config_id: Optional[int] = None):
        """Load configuration from database."""
        if not self.config_service:
            logger.warning("No database session available for loading config")
            return
        
        try:
            config_dict = self.config_service.get_config_dict(config_id)
            self.update_config(config_dict)
            logger.info(f"Loaded configuration from database (ID: {config_id})")
        except Exception as e:
            logger.error(f"Error loading config from database: {str(e)}")
            raise
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        tools = []
        for tool_name, tool in self.tool_registry._tools.items():
            tools.append({
                "name": tool.get_name(),
                "description": tool.get_description(),
                "parameters": [{
                    "name": param.name,
                    "type": param.type.value,
                    "description": param.description,
                    "required": param.required,
                    "default": param.default,
                    "enum": param.enum
                } for param in tool.get_parameters()],
                "enabled": tool_name in self.config.enabled_tools
            })
        return tools
    
    def get_config(self) -> Dict[str, Any]:
        """Get current agent configuration."""
        return self.config.dict()


# Global agent service instance
_agent_service: Optional[AgentService] = None


def get_agent_service(db_session=None) -> AgentService:
    """Get global agent service instance."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService(db_session)
    elif db_session and not _agent_service.db_session:
        # Update with database session if not already set
        _agent_service.db_session = db_session
        _agent_service.config_service = AgentConfigService(db_session)
        _agent_service._load_config()
    return _agent_service