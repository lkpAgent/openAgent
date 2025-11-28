"""
MCP服务HTTP REST API接口
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
import os

from .config import MCPServerConfig
from .manager import get_mcp_manager, initialize_mcp_manager

from mcpserver.utils.logger import get_logger

logger = get_logger("mcp_api")


# Pydantic模型定义
class ToolExecuteRequest(BaseModel):
    """工具执行请求模型"""
    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


class ToolExecuteResponse(BaseModel):
    """工具执行响应模型"""
    success: bool = Field(..., description="执行是否成功")
    result: Optional[Any] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    tool_name: str = Field(..., description="工具名称")
    executed_at: str = Field(..., description="执行时间")


class ToolInfo(BaseModel):
    """工具信息模型"""
    name: str = Field(..., description="工具名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="工具描述")
    parameters: List[Dict[str, Any]] = Field(..., description="工具参数")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    initialized: bool = Field(..., description="是否已初始化")
    tools_count: int = Field(..., description="工具数量")
    available_tools: List[str] = Field(..., description="可用工具列表")
    timestamp: str = Field(..., description="检查时间")


# 全局变量
mcp_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global mcp_manager
    
    # 启动时初始化
    logger.info("启动MCP服务器...")
    # 加载 mcpserver 目录下的 .env，使工具可通过 os.getenv 读取密钥
    try:
        env_path = Path(__file__).parent / ".env"
        logger.info(f"准备加载环境变量文件: {env_path}，存在: {env_path.exists()}")
        load_dotenv(dotenv_path=env_path, override=True)
        logger.info(f"已加载环境变量文件: {env_path}")
        # 直接读取原始 .env 内容用于调试
        try:
            size = env_path.stat().st_size
            raw = env_path.read_text(encoding="utf-8")
            logger.info(f".env 文件大小: {size}，原始内容长度: {len(raw)}, 预览: {raw!r}")
        except Exception as e:
            logger.warning(f".env 读取失败: {e}")
        # 读取原始 .env 内容，作为回退
        env_values = dotenv_values(env_path)
        logger.info(f".env 中包含键: {list(env_values.keys())}")
        if not os.getenv("WEATHER_API_KEY") and env_values.get("WEATHER_API_KEY"):
            os.environ["WEATHER_API_KEY"] = env_values["WEATHER_API_KEY"]
            logger.info("回退设置 WEATHER_API_KEY 至进程环境")
        logger.info(f"启动时检测 WEATHER_API_KEY: {'已配置' if os.getenv('WEATHER_API_KEY') else '未配置'}")
    except Exception as e:
        logger.warning(f".env 加载失败: {e}")
    
    config = MCPServerConfig()
    mcp_manager = await initialize_mcp_manager(config)
    logger.info("MCP服务器启动完成")
    
    yield
    
    # 关闭时清理
    logger.info("关闭MCP服务器...")
    if mcp_manager:
        await mcp_manager.shutdown()
    logger.info("MCP服务器已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="MCP服务器",
    description="统一的MCP工具服务HTTP REST API",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_manager():
    """获取MCP管理器依赖"""
    global mcp_manager
    if mcp_manager is None:
        raise HTTPException(status_code=503, detail="MCP服务管理器未初始化")
    return mcp_manager


@app.get("/", summary="根路径", description="返回服务基本信息")
async def root():
    """根路径"""
    return {
        "service": "MCP服务器",
        "version": "1.0.0",
        "description": "统一的MCP工具服务HTTP REST API",
        "endpoints": {
            "health": "/health",
            "tools": "/tools",
            "execute": "/execute"
        }
    }


@app.get("/health", response_model=HealthResponse, summary="健康检查", description="检查服务健康状态")
async def health_check(manager=Depends(get_manager)):
    """健康检查"""
    try:
        health_info = await manager.health_check()
        return HealthResponse(**health_info)
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@app.get("/tools", response_model=List[ToolInfo], summary="获取工具列表", description="获取所有可用工具的信息")
async def list_tools(manager=Depends(get_manager)):
    """获取工具列表"""
    try:
        tools_info = manager.list_tools()
        return [ToolInfo(**tool) for tool in tools_info]
    except Exception as e:
        logger.error(f"获取工具列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")


@app.get("/tools/{tool_name}", response_model=ToolInfo, summary="获取工具信息", description="获取指定工具的详细信息")
async def get_tool_info(tool_name: str, manager=Depends(get_manager)):
    """获取指定工具信息"""
    try:
        tools_info = manager.list_tools()
        for tool in tools_info:
            if tool["name"] == tool_name:
                return ToolInfo(**tool)
        
        raise HTTPException(status_code=404, detail=f"工具 '{tool_name}' 不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取工具信息失败: {str(e)}")


@app.post("/execute", response_model=ToolExecuteResponse, summary="执行工具", description="执行指定的工具操作")
async def execute_tool(request: ToolExecuteRequest, manager=Depends(get_manager)):
    """执行工具"""
    try:
        # 调试输入参数，观察编码与类型
        loc = request.parameters.get('location', None)
        logger.info(f"/execute 收到请求: tool={request.tool_name}, parameters={request.parameters}")
        if loc is not None:
            logger.info(f"location 参数类型: {type(loc)}, 值repr: {loc!r}")
        result = await manager.execute_tool(request.tool_name, **request.parameters)
        return ToolExecuteResponse(**result)
    except Exception as e:
        logger.error(f"执行工具失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行工具失败: {str(e)}")


@app.post("/tools/{tool_name}/execute", response_model=ToolExecuteResponse, summary="执行指定工具", description="执行指定名称的工具操作")
async def execute_specific_tool(tool_name: str, parameters: Dict[str, Any], manager=Depends(get_manager)):
    """执行指定工具"""
    try:
        result = await manager.execute_tool(tool_name, **parameters)
        return ToolExecuteResponse(**result)
    except Exception as e:
        logger.error(f"执行工具失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行工具失败: {str(e)}")


# MySQL专用接口
@app.post("/mysql/connect", summary="MySQL连接", description="连接到MySQL数据库")
async def mysql_connect(
    connection_config: Dict[str, Any],
    user_id: str,
    manager=Depends(get_manager)
):
    """MySQL数据库连接"""
    return await execute_tool(
        ToolExecuteRequest(
            tool_name="mysql",
            parameters={
                "action": "connect",
                "connection_config": connection_config,
                "user_id": user_id
            }
        ),
        manager
    )


@app.post("/mysql/query", summary="MySQL查询", description="执行MySQL查询")
async def mysql_query(
    user_id: str,
    sql_query: str,
    limit: int = 100,
    manager=Depends(get_manager)
):
    """MySQL查询"""
    return await execute_tool(
        ToolExecuteRequest(
            tool_name="mysql",
            parameters={
                "operation": "execute_query",
                "user_id": user_id,
                "sql_query": sql_query,
                "limit": limit
            }
        ),
        manager
    )


# PostgreSQL专用接口
@app.post("/postgresql/connect", summary="PostgreSQL连接", description="连接到PostgreSQL数据库")
async def postgresql_connect(
    connection_config: Dict[str, Any],
    user_id: str,
    manager=Depends(get_manager)
):
    """PostgreSQL数据库连接"""
    return await execute_tool(
        ToolExecuteRequest(
            tool_name="postgresql",
            parameters={
                "operation": "connect",
                "connection_config": connection_config,
                "user_id": user_id
            }
        ),
        manager
    )


@app.post("/postgresql/query", summary="PostgreSQL查询", description="执行PostgreSQL查询")
async def postgresql_query(
    user_id: str,
    sql_query: str,
    limit: int = 100,
    manager=Depends(get_manager)
):
    """PostgreSQL查询"""
    return await execute_tool(
        ToolExecuteRequest(
            tool_name="postgresql",
            parameters={
                "operation": "execute_query",
                "user_id": user_id,
                "sql_query": sql_query,
                "limit": limit
            }
        ),
        manager
    )


def create_app(config: Optional[MCPServerConfig] = None) -> FastAPI:
    """创建FastAPI应用实例"""
    return app


def run_server(host: str = "0.0.0.0", port: int = 8002, reload: bool = False):
    """运行MCP服务器"""
    logger.info(f"启动MCP服务器，地址: http://{host}:{port}")
    uvicorn.run(
        "mcpserver.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    # 直接运行时的配置
    config = MCPServerConfig()
    run_server(
        host=config.HOST,
        port=config.PORT,
        reload=False
    )