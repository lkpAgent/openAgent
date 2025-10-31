"""Agent services package.

轻量化导入：仅暴露基础工具类型，避免在包导入时加载耗时的服务层。使用 AgentService 时请从子模块显式导入：
    from open_agent.services.agent.agent_service import AgentService
"""

from .base import BaseTool, ToolRegistry

__all__ = [
    "BaseTool",
    "ToolRegistry"
]