"""Agent tools package."""

from .calculator import CalculatorTool
from .weather import WeatherTool
from .search import SearchTool
from .datetime_tool import DateTimeTool
from .file_tool import FileTool
from .generate_image import GenerateImageTool

# Try to import decorated tools if available
try:
    from .example_decorated_tool import DECORATED_TOOLS
except ImportError:
    DECORATED_TOOLS = []

# Try to import LangChain native tools if available
try:
    from .langchain_native_tools import LANGCHAIN_NATIVE_TOOLS
except ImportError:
    LANGCHAIN_NATIVE_TOOLS = []

__all__ = [
    'CalculatorTool',
    'WeatherTool', 
    'SearchTool',
    'DateTimeTool',
    'GenerateImageTool',
    'FileTool',
    'DECORATED_TOOLS',
    'LANGCHAIN_NATIVE_TOOLS'
]