"""openAgent - A modern chat agent application."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "A modern chat agent application with Vue frontend and FastAPI backend"

# 轻量化初始化：避免在导入 open_agent 包时加载全局配置
# 如需使用，请直接从子模块导入：
#   - 配置：`from open_agent.core.config import get_settings, Settings`
#   - 应用工厂：`from open_agent.core.app import create_app`

__all__ = ["__version__"]