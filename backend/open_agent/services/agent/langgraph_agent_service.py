"""LangGraph Agent service with tool calling capabilities."""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
# from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from .base import ToolRegistry
from open_agent.services.tools import WeatherQueryTool, TavilySearchTool, DateTimeTool
from ..postgresql_tool_manager import get_postgresql_tool
from ...core.config import get_settings
from ...utils.logger import get_logger
from ..agent_config import AgentConfigService
from open_agent.services.mcp.mcp_dynamic_tools import load_mcp_tools

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
    """LangGraph Agent service using low-level LangGraph graph (React pattern)."""
    
    def __init__(self, db_session=None):
        self.settings = get_settings()
        self.tool_registry = ToolRegistry()
        self.config = LangGraphAgentConfig()
        self.tools = []
        self.db_session = db_session
        self.config_service = AgentConfigService(db_session) if db_session else None
        self._initialize_tools()
        self._load_config()
        self._create_react_agent()
        
    def _initialize_tools(self):
        """Initialize available tools."""
        try:
            dynamic_tools = load_mcp_tools()
        except Exception as e:
            logger.warning(f"加载 MCP 动态工具失败，使用本地工具回退: {e}")
            dynamic_tools = []

        # Always keep DateTimeTool locally
        base_tools = [DateTimeTool()]

        if dynamic_tools:
            self.tools = dynamic_tools + base_tools
            logger.info(f"LangGraph 绑定 MCP 动态工具: {[t.name for t in dynamic_tools]}")
        else:
            # Fallback to local weather/search when MCP not available
            self.tools = [
                WeatherQueryTool(),
                TavilySearchTool(),
            ] + base_tools
            logger.info("MCP 不可用，已回退到本地 Weather/Search 工具")


            
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
                

        
    def _create_react_agent(self):
        """Create LangGraph agent using low-level StateGraph with explicit nodes/edges."""
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
            
            # Bind tools to the model so it can propose tool calls
            try:
                # 下面的提示词并不必需，因为langchain的function call内部机制已经设定了底层提示词。除非确定需要自定义，比如让大模型思考过程侧重于哪些方面，才有必要加上。
                react_system_prompt = """# 角色定位
                你是一个专业的智能体协调大师，擅长精准调度各类工具资源来解决复杂问题。你的核心能力是准确判断问题性质并选择最合适的工具。

                # 工具调用原则

                ## 1. 工具选择标准
                **外部搜索工具适用场景：**
                - 实时性信息（天气、新闻、股价等）
                - 公开知识查询（概念解释、事实核查）
                - 动态数据获取（汇率、趋势分析）
                - 需要最新外部信息的场景

                **内部数据库查询适用场景：**
                - 内部业务数据检索
                - 用户个人信息查询
                - 结构化数据查找
                - 敏感或私有信息处理
                
                要求每一步思考时，都要给出思考过程与结果
                """

                self.bound_model = self.model.bind_tools(self.tools)
            except Exception as e:
                logger.warning(f"Failed to bind tools to model, tool calling may not work: {e}")
                self.bound_model = self.model

            # Build low-level React graph: State -> agent -> tools -> agent ... until stop
            from typing import TypedDict
            from langgraph.graph import StateGraph, START, END
            from langchain_core.messages import ToolMessage, BaseMessage
            from typing import Annotated
            from langgraph.graph.message import add_messages

            class AgentState(TypedDict):
                messages: Annotated[List[BaseMessage], add_messages]

            # Node: call the model
            def agent_node(state: AgentState) -> AgentState:
                messages = state["messages"]

                # 确保有系统提示
                if not any(isinstance(msg, SystemMessage) for msg in messages):
                    messages = [SystemMessage(content=react_system_prompt)] + messages
                # Optionally include a system instruction at the start for first turn
                if messages and messages[0].__class__.__name__ != 'SystemMessage':
                    # Keep user history untouched; rely on upstream to include system if desired
                    pass
                ai = self.bound_model.invoke(messages)
                return {"messages": [ai]}

            # Node: execute tools requested by the last AI message
            def tools_node(state: AgentState) -> AgentState:
                messages = state["messages"]
                last = messages[-1]
                outputs: List[ToolMessage] = []
                try:
                    tool_calls = getattr(last, 'tool_calls', []) or []
                    tool_map = {t.name: t for t in self.tools}
                    for call in tool_calls:
                        name = call.get('name') if isinstance(call, dict) else getattr(call, 'name', None)
                        args = call.get('args') if isinstance(call, dict) else getattr(call, 'args', {})
                        call_id = call.get('id') if isinstance(call, dict) else getattr(call, 'id', '')
                        if name in tool_map:
                            try:
                                result = tool_map[name].invoke(args)
                            except Exception as te:
                                result = f"Tool {name} execution error: {te}"
                        else:
                            result = f"Unknown tool: {name}"
                        outputs.append(ToolMessage(content=str(result), tool_call_id=call_id))
                except Exception as e:
                    outputs.append(ToolMessage(content=f"Tool execution error: {e}", tool_call_id=""))
                return {"messages": outputs}

            # Router: decide next step after agent node
            def route_after_agent(state: AgentState) -> str:
                last = state["messages"][-1]
                finish_reason = None
                try:
                    meta = getattr(last, 'response_metadata', {}) or {}
                    finish_reason = meta.get('finish_reason')
                except Exception:
                    finish_reason = None
                # If the model decided to call tools, continue to tools node
                if getattr(last, 'tool_calls', None):
                    return "tools"
                # Otherwise, end
                return END

            graph = StateGraph(AgentState)
            graph.add_node("agent", agent_node)
            graph.add_node("tools", tools_node)
            graph.add_edge(START, "agent")
            graph.add_conditional_edges("agent", route_after_agent, {"tools": "tools", END: END})
            graph.add_edge("tools", "agent")
            
            # Compile graph and store as self.agent for compatibility with existing code
            self.react_agent = graph.compile()
            
            logger.info("LangGraph low-level React agent created successfully")
            
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
            
            # Use the low-level graph directly
            result = await self.react_agent.ainvoke({"messages": messages}, {"recursion_limit": 6}, )
            
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
            async for event in self.react_agent.astream({"messages": messages}):
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
                                        thinking_content = " 正在思考..."
                                        if hasattr(last_msg, 'content') and last_msg.content:
                                            thinking_content = f" 思考: {last_msg.content[:200]}..."
                                        elif isinstance(last_msg, dict) and "content" in last_msg:
                                            thinking_content = f" 思考: {last_msg['content'][:200]}..."

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
                                            "content": f" 执行步骤: {node_name}",
                                            "node_name": node_name,
                                            "raw_output": str(node_output)[:500] if node_output else "",
                                            "done": False
                                        }
                                        await asyncio.sleep(0.1)

                        # 处理其他节点
                        else:
                            yield {
                                "type": "step",
                                "content": f" 执行步骤: {node_name}",
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
        self._create_react_agent()
        logger.info("Agent configuration updated")

    def _create_plan_execute_agent(self):
        """Create a Plan-and-Execute agent using LangGraph low-level API.
        结构：START -> planner -> executor(loop) -> summarize -> END
        - planner：根据用户问题生成计划（JSON 数组）
        - executor：逐步执行计划（可调用工具），收集每步结果
        - summarize：综合计划与执行结果产出最终回答
        """
        from typing import TypedDict, Annotated, List
        import json
        from langgraph.graph import StateGraph, START, END
        from langgraph.graph.message import add_messages
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
        try:
            self.bound_model = self.model.bind_tools(self.tools)
        except Exception as e:
            logger.warning(f"Failed to bind tools to model, tool calling may not work: {e}")
            self.bound_model = self.model
        class PlanState(TypedDict):
            messages: Annotated[List[BaseMessage], add_messages]
            plan_steps: List[str]
            current_step: int
            step_results: List[str]

        def planner_node(state: PlanState) -> PlanState:
            messages = state.get("messages", [])
            plan_prompt = (
                "你是规划助手。基于对话内容生成可执行计划，" 
                "用 JSON 数组返回，每个元素是一条明确且可操作的步骤。" 
                "仅输出 JSON，不要额外解释。"
            )
            ai_plan = self.model.invoke(messages + [HumanMessage(content=plan_prompt)])
            steps: List[str] = []
            try:
                parsed = json.loads(ai_plan.content)
                if isinstance(parsed, list):
                    steps = [str(s) for s in parsed]
            except Exception:
                # 回退：按行拆分
                steps = [s.strip() for s in ai_plan.content.split("\n") if s.strip()]
            return {
                "messages": [ai_plan],
                "plan_steps": steps,
                "current_step": 0,
                "step_results": []
            }

        def executor_node(state: PlanState) -> PlanState:
            idx = state.get("current_step", 0)
            steps = state.get("plan_steps", [])
            msgs = state.get("messages", [])
            if idx >= len(steps):
                return {"messages": [], "current_step": idx, "step_results": state.get("step_results", [])}

            step_text = steps[idx]
            exec_prompt = (
                f"请执行计划的第{idx+1}步：{step_text}。" 
                "需要用工具时创建工具调用；完成后给出该步的结果。"
            )
            ai_exec = self.bound_model.invoke(msgs + [HumanMessage(content=exec_prompt)])

            new_messages: List[BaseMessage] = [ai_exec]
            step_result_content = None

            # 处理工具调用
            tool_map = {t.name: t for t in self.tools}
            tool_msgs: List[ToolMessage] = []
            tool_calls = getattr(ai_exec, "tool_calls", []) or (ai_exec.additional_kwargs.get("tool_calls") if hasattr(ai_exec, "additional_kwargs") else [])
            if tool_calls:
                for call in tool_calls:
                    name = call.get("name")
                    args = call.get("args", {})
                    tool_obj = tool_map.get(name)
                    if tool_obj:
                        try:
                            result = tool_obj.invoke(args)
                        except Exception as e:
                            result = f"工具执行失败: {e}"
                    else:
                        result = f"未找到工具: {name}"
                    tool_call_id = call.get("id") or call.get("tool_call_id") or call.get("call_id") or f"tool_{name}"
                    tool_msgs.append(ToolMessage(content=str(result), tool_call_id=tool_call_id, name=name or "tool"))
                new_messages.extend(tool_msgs)
                # 基于工具输出总结该步结果
                summarize_step = "请基于上述工具输出，总结该步骤的结果，给出结构化要点与可读说明。"
                ai_step = self.bound_model.invoke(msgs + [ai_exec] + tool_msgs + [HumanMessage(content=summarize_step)])
                step_result_content = ai_step.content
                new_messages.append(ai_step)
            else:
                step_result_content = ai_exec.content

            all_results = list(state.get("step_results", []))
            if step_result_content:
                all_results.append(step_result_content)

            return {
                "messages": new_messages,
                "current_step": idx + 1,
                "step_results": all_results
            }

        def route_after_planner(state: PlanState) -> str:
            return "executor" if state.get("plan_steps") else END

        def route_after_executor(state: PlanState) -> str:
            cur = state.get("current_step", 0)
            total = len(state.get("plan_steps", []))
            return "executor" if cur < total else "summarize"

        def summarize_node(state: PlanState) -> PlanState:
            import json as _json
            msgs = state.get("messages", [])
            steps = state.get("plan_steps", [])
            results = state.get("step_results", [])
            final_prompt = (
                "请综合以上计划与各步骤结果，生成最终回答。" 
                "要求：逻辑清晰、结论明确、可读性强；如存在不确定性请注明。"
            )
            context_msg = HumanMessage(content=(
                f"计划: {_json.dumps(steps, ensure_ascii=False)}\n"
                f"步骤结果: {_json.dumps(results, ensure_ascii=False)}\n"
                f"{final_prompt}"
            ))
            ai_final = self.model.invoke(msgs + [context_msg])
            return {"messages": [ai_final]}

        graph = StateGraph(PlanState)
        graph.add_node("planner", planner_node)
        graph.add_node("executor", executor_node)
        graph.add_node("summarize", summarize_node)
        graph.add_edge(START, "planner")
        graph.add_conditional_edges("planner", route_after_planner, {"executor": "executor", END: END})
        graph.add_conditional_edges("executor", route_after_executor, {"executor": "executor", "summarize": "summarize"})
        graph.add_edge("summarize", END)

        self.plan_execute_agent = graph.compile()

    async def chat_plan_execute(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Single-turn Plan-and-Execute chat."""
        # 确保 agent 已创建
        if not hasattr(self, "plan_execute_agent"):
            self._create_plan_execute_agent()

        # 构建消息
        messages = []
        if chat_history:
            for msg in chat_history:
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                else:
                    messages.append(AIMessage(content=content))
        messages.append(HumanMessage(content=message))

        try:
            result = await self.plan_execute_agent.ainvoke({"messages": messages}, config={"recursion_limit": self.config.max_iterations})
            final_msg = None
            if isinstance(result, dict) and "messages" in result:
                ms = result["messages"]
                if ms:
                    final_msg = ms[-1]
            final_text = getattr(final_msg, "content", "") if final_msg else ""
            return {
                "status": "success",
                "response": final_text,
                "raw": str(result)
            }
        except Exception as e:
            logger.error(f"Error in chat_plan_execute: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def chat_stream_plan_execute(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Streamed Plan-and-Execute chat."""
        import asyncio as _asyncio
        if not hasattr(self, "plan_execute_agent"):
            self._create_plan_execute_agent()

        messages = []
        if chat_history:
            for msg in chat_history:
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                else:
                    messages.append(AIMessage(content=content))
        messages.append(HumanMessage(content=message))

        try:
            accumulated = ""
            async for event in self.react_agent.astream({"messages": messages}, config={"recursion_limit": self.config.max_iterations}):
                for key, node_output in event.items():
                    node_name = key[0] if isinstance(key, tuple) else key
                    if node_name == "planner":
                        # 规划阶段
                        content = "生成计划中..."
                        if node_output and isinstance(node_output, dict):
                            m = node_output.get("messages", [])
                            if m:
                                last = m[-1]
                                if hasattr(last, "content"):
                                    content = str(last.content)[:400]
                        yield {"type": "planning", "content": content, "done": False}
                        await _asyncio.sleep(0.05)
                    elif node_name == "executor":
                        # 执行阶段（可能包含工具）
                        yield {"type": "step", "content": "执行计划步骤", "done": False}
                        await _asyncio.sleep(0.05)
                        if node_output and isinstance(node_output, dict):
                            msgs = node_output.get("messages", [])
                            # 输出工具结束标记
                            tool_msgs = [m for m in msgs if hasattr(m, "__class__") and "Tool" in m.__class__.__name__]
                            if tool_msgs:
                                yield {"type": "tools_end", "content": f"完成 {len(tool_msgs)} 次工具执行", "done": False}
                                await _asyncio.sleep(0.03)
                            # 尝试输出该步总结
                            ai_msgs = [m for m in msgs if hasattr(m, "__class__") and "AI" in m.__class__.__name__]
                            if ai_msgs:
                                text = ai_msgs[-1].content
                                if text:
                                    accumulated = text
                                    yield {"type": "response", "content": accumulated, "done": False}
                                    await _asyncio.sleep(0.02)
                    elif node_name == "summarize":
                        # 最终总结
                        if node_output and isinstance(node_output, dict):
                            msgs = node_output.get("messages", [])
                            if msgs:
                                final = msgs[-1]
                                content = getattr(final, "content", "")
                                if content:
                                    yield {"type": "response_start", "content": "", "done": False}
                                    yield {"type": "response", "content": content, "done": False}
                                    accumulated = content
                                    await _asyncio.sleep(0.02)
            yield {"type": "complete", "content": accumulated, "done": True}
        except Exception as e:
            logger.error(f"Error in chat_stream_plan_execute: {e}", exc_info=True)
            yield {"type": "error", "content": str(e), "done": True}


# Global instance
_langgraph_agent_service: LangGraphAgentService = None


def get_langgraph_agent_service(db_session=None) -> LangGraphAgentService:
    """Get or create LangGraph agent service instance."""
    global _langgraph_agent_service
    
    if _langgraph_agent_service is None:
        _langgraph_agent_service = LangGraphAgentService(db_session)
        logger.info("LangGraph Agent service initialized")
        
    return _langgraph_agent_service