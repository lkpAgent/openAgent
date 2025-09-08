"""数据库配置管理API"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from chat_agent.models.user import User
from chat_agent.db.database import get_db
from chat_agent.services.database_config_service import DatabaseConfigService
from chat_agent.utils.logger import get_logger
from chat_agent.services.auth import AuthService
logger = get_logger("database_config_api")
router = APIRouter(prefix="/api/database-config", tags=["database-config"])
from chat_agent.utils.schemas import FileListResponse,ExcelPreviewRequest,NormalResponse

# 在文件顶部添加
from functools import lru_cache

# 创建服务单例
@lru_cache()
def get_database_config_service() -> DatabaseConfigService:
    """获取DatabaseConfigService单例"""
    # 注意：这里需要处理db session的问题
    return DatabaseConfigService(None)  # 临时方案

# 或者使用全局变量
_database_service_instance = None

def get_database_service(db: Session = Depends(get_db)) -> DatabaseConfigService:
    """获取DatabaseConfigService实例"""
    global _database_service_instance
    if _database_service_instance is None:
        _database_service_instance = DatabaseConfigService(db)
    else:
        # 更新db session
        _database_service_instance.db = db
    return _database_service_instance
class DatabaseConfigCreate(BaseModel):
    name: str = Field(..., description="配置名称")
    db_type: str = Field(default="postgresql", description="数据库类型")
    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口号")
    database: str = Field(..., description="数据库名")
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    is_default: bool = Field(default=False, description="是否为默认配置")
    connection_params: Dict[str, Any] = Field(default=None, description="额外连接参数")


class DatabaseConfigResponse(BaseModel):
    id: int
    name: str
    db_type: str
    host: str
    port: int
    database: str
    username: str
    password: str  # 添加密码字段
    is_active: bool
    is_default: bool
    created_at: str
    updated_at: str = None


@router.post("/", response_model=NormalResponse)
async def create_database_config(
    config_data: DatabaseConfigCreate,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """创建或更新数据库配置"""
    try:
        service = DatabaseConfigService(db)
        config = await service.create_or_update_config(current_user.id, config_data.dict())
        return NormalResponse(
                success=True,
                message="保存数据库配置成功",
                data=config
            )
    except Exception as e:
        logger.error(f"创建或更新数据库配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[DatabaseConfigResponse])
async def get_database_configs(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的数据库配置列表"""
    try:
        service = DatabaseConfigService(db)
        configs = service.get_user_configs(current_user.id)
        return [config.to_dict(include_password=True, decrypt_service=service) for config in configs]
    except Exception as e:
        logger.error(f"获取数据库配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{config_id}/test")
async def test_database_connection(
    config_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """测试数据库连接"""
    try:
        service = DatabaseConfigService(db)
        result = await service.test_connection(config_id, current_user.id)
        return result
    except Exception as e:
        logger.error(f"测试数据库连接失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{config_id}/connect")
async def connect_database(
    config_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    service: DatabaseConfigService = Depends(get_database_service)
):
    """连接数据库并获取表列表"""
    try:
        result = await service.connect_and_get_tables(config_id, current_user.id)
        return result
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/tables/{table_name}/data")
async def get_table_data(
    table_name: str,
    limit: int = 100,
    current_user: User = Depends(AuthService.get_current_user),
    service: DatabaseConfigService = Depends(get_database_service)
):
    """获取表数据预览"""
    try:
        result = await service.get_table_data(table_name, current_user.id, limit)
        return result
    except Exception as e:
        logger.error(f"获取表数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/tables/{table_name}/schema")
async def get_table_schema(
    table_name: str,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """获取表结构信息"""
    try:
        service = DatabaseConfigService(db)
        result = await service.describe_table(table_name, current_user.id)
        return result
    except Exception as e:
        logger.error(f"获取表结构失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/by-type/{db_type}", response_model=DatabaseConfigResponse)
async def get_config_by_type(
    db_type: str,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """根据数据库类型获取配置"""
    try:
        service = DatabaseConfigService(db)
        config = service.get_config_by_type(current_user.id, db_type)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到类型为 {db_type} 的配置"
            )
        # 返回包含解密密码的配置
        return config.to_dict(include_password=True, decrypt_service=service)
    except Exception as e:
        logger.error(f"获取数据库配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

