"""ChatAgent - A modern chat agent application."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "A modern chat agent application with Vue frontend and FastAPI backend"

# 导出主要组件
from .core.config import settings
from .core.app import create_app

__all__ = ["settings", "create_app", "__version__"]