# 自定义工具开发指南

本指南将详细介绍如何在Chat Agent系统中创建自定义工具。

## 1. 工具系统架构

### 核心组件
- **BaseTool**: 所有工具的基类
- **ToolParameter**: 工具参数定义
- **ToolResult**: 工具执行结果
- **ToolRegistry**: 工具注册管理器

### 工具接口
每个工具必须继承`BaseTool`并实现以下方法：
- `get_name()`: 返回工具名称
- `get_description()`: 返回工具描述
- `get_parameters()`: 返回工具参数列表
- `execute(**kwargs)`: 执行工具逻辑

## 2. 创建自定义工具

### 步骤1: 创建工具文件

在`backend/chat_agent/services/agent/tools/`目录下创建新的Python文件，例如`my_custom_tool.py`：

```python
"""自定义工具示例。"""

import asyncio
from typing import List, Dict, Any
from ..base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from ....utils.logger import get_logger

logger = get_logger("my_custom_tool")


class MyCustomTool(BaseTool):
    """自定义工具示例。"""
    
    def get_name(self) -> str:
        """返回工具名称。"""
        return "my_custom_tool"
    
    def get_description(self) -> str:
        """返回工具描述。"""
        return "这是一个自定义工具示例，用于演示如何创建新工具"
    
    def get_parameters(self) -> List[ToolParameter]:
        """定义工具参数。"""
        return [
            ToolParameter(
                name="input_text",
                type=ToolParameterType.STRING,
                description="输入文本",
                required=True
            ),
            ToolParameter(
                name="count",
                type=ToolParameterType.INTEGER,
                description="处理次数",
                required=False,
                default=1
            ),
            ToolParameter(
                name="uppercase",
                type=ToolParameterType.BOOLEAN,
                description="是否转换为大写",
                required=False,
                default=False
            )
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具逻辑。"""
        try:
            # 获取参数
            input_text = kwargs.get("input_text")
            count = kwargs.get("count", 1)
            uppercase = kwargs.get("uppercase", False)
            
            # 参数验证
            if not input_text:
                return ToolResult(
                    success=False,
                    error="input_text参数是必需的"
                )
            
            logger.info(f"处理文本: {input_text}, 次数: {count}, 大写: {uppercase}")
            
            # 执行工具逻辑
            result_text = input_text
            
            # 重复处理
            for i in range(count):
                result_text = f"[{i+1}] {result_text}"
            
            # 大写转换
            if uppercase:
                result_text = result_text.upper()
            
            # 模拟异步操作
            await asyncio.sleep(0.1)
            
            return ToolResult(
                success=True,
                result={
                    "processed_text": result_text,
                    "original_text": input_text,
                    "processing_count": count,
                    "is_uppercase": uppercase
                },
                metadata={
                    "tool_version": "1.0.0",
                    "processing_time": "0.1s"
                }
            )
            
        except Exception as e:
            logger.error(f"工具执行失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"工具执行失败: {str(e)}"
            )
```

### 步骤2: 注册工具

在`backend/chat_agent/services/agent/tools/__init__.py`文件中导入并导出新工具：

```python
from .my_custom_tool import MyCustomTool

__all__ = [
    "CalculatorTool",
    "WeatherTool", 
    "SearchTool",
    "DateTimeTool",
    "FileTool",
    "MyCustomTool"  # 添加新工具
]
```

### 步骤3: 在Agent服务中注册

在`backend/chat_agent/services/agent/agent_service.py`中注册工具：

```python
from .tools import MyCustomTool

class AgentService:
    def __init__(self):
        # ... 其他初始化代码
        
        # 注册工具
        self.tool_registry.register(MyCustomTool(), enabled=True)
```

## 3. 参数类型说明

### 支持的参数类型
- `STRING`: 字符串类型
- `INTEGER`: 整数类型
- `FLOAT`: 浮点数类型
- `BOOLEAN`: 布尔类型
- `ARRAY`: 数组类型
- `OBJECT`: 对象类型

### 参数配置选项
- `name`: 参数名称
- `type`: 参数类型
- `description`: 参数描述
- `required`: 是否必需（默认True）
- `default`: 默认值
- `enum`: 枚举值列表

### 参数示例

```python
ToolParameter(
    name="mode",
    type=ToolParameterType.STRING,
    description="处理模式",
    required=True,
    enum=["fast", "normal", "detailed"]
),
ToolParameter(
    name="options",
    type=ToolParameterType.OBJECT,
    description="配置选项",
    required=False,
    default={"timeout": 30}
)
```

## 4. 最佳实践

### 错误处理
- 始终使用try-catch包装执行逻辑
- 返回有意义的错误信息
- 记录详细的日志信息

### 参数验证
- 验证必需参数是否存在
- 检查参数类型和范围
- 提供合理的默认值

### 异步支持
- 所有工具的execute方法都是异步的
- 对于耗时操作，使用await
- 避免阻塞主线程

### 日志记录
- 使用统一的日志记录器
- 记录关键操作和错误信息
- 包含足够的上下文信息

## 5. 测试工具

### 创建测试脚本

```python
#!/usr/bin/env python3
"""测试自定义工具。"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from open_agent.services.tools import MyCustomTool


async def test_custom_tool():
    """测试自定义工具。"""
    print("=== 测试自定义工具 ===")

    try:
        # 创建工具实例
        tool = MyCustomTool()
        print(f"✓ 工具创建成功: {tool.get_name()}")
        print(f"✓ 工具描述: {tool.get_description()}")

        # 测试工具执行
        result = await tool.execute(
            input_text="Hello World",
            count=3,
            uppercase=True
        )

        if result.success:
            print("✓ 工具执行成功!")
            print(f"✓ 结果: {result.result}")
            return True
        else:
            print(f"✗ 工具执行失败: {result.error}")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_custom_tool())
    if not success:
        sys.exit(1)
```

## 6. 高级功能

### 工具配置
可以为工具添加配置选项：

```python
class MyCustomTool(BaseTool):
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        super().__init__()
```

### 工具依赖
如果工具需要外部依赖，在工具初始化时检查：

```python
def __init__(self):
    try:
        import some_required_library
        self.library = some_required_library
    except ImportError:
        raise ImportError("需要安装 some_required_library")
    super().__init__()
```

### 工具缓存
对于耗时操作，可以添加缓存机制：

```python
from functools import lru_cache

class MyCustomTool(BaseTool):
    @lru_cache(maxsize=100)
    def _expensive_operation(self, input_data):
        # 耗时操作
        return result
```

## 7. 部署和使用

1. **重启服务**: 添加新工具后需要重启后端服务
2. **工具启用**: 确保工具在Agent配置中被启用
3. **测试集成**: 通过聊天API测试工具调用

### API测试示例

```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "请使用my_custom_tool处理文本Hello",
    "use_agent": true
  }'
```

## 8. 故障排除

### 常见问题
1. **工具未注册**: 检查__init__.py导入和agent_service.py注册
2. **参数错误**: 验证参数定义和传递
3. **异步问题**: 确保execute方法正确使用async/await
4. **依赖缺失**: 检查所需的Python包是否已安装

### 调试技巧
- 查看日志文件获取详细错误信息
- 使用测试脚本独立测试工具
- 检查工具注册状态
- 验证参数传递和类型

通过遵循本指南，您可以成功创建和部署自定义工具，扩展Chat Agent系统的功能。