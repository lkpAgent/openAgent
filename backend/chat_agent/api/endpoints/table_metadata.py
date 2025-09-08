"""表元数据管理API"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from chat_agent.models.user import User
from chat_agent.db.database import get_db
from chat_agent.services.table_metadata_service import TableMetadataService
from chat_agent.utils.logger import get_logger
from chat_agent.services.auth import AuthService

logger = get_logger("table_metadata_api")
router = APIRouter(prefix="/api/table-metadata", tags=["table-metadata"])


class TableSelectionRequest(BaseModel):
    database_config_id: int = Field(..., description="数据库配置ID")
    table_names: List[str] = Field(..., description="选中的表名列表")


class TableMetadataResponse(BaseModel):
    id: int
    table_name: str
    table_schema: str
    table_type: str
    table_comment: str
    columns_count: int
    row_count: int
    is_enabled_for_qa: bool
    qa_description: str
    business_context: str
    last_synced_at: str


class QASettingsUpdate(BaseModel):
    is_enabled_for_qa: bool = Field(default=True)
    qa_description: str = Field(default="")
    business_context: str = Field(default="")


class TableByNameRequest(BaseModel):
    database_config_id: int = Field(..., description="数据库配置ID")
    table_name: str = Field(..., description="表名")


@router.post("/collect")
async def collect_table_metadata(
    request: TableSelectionRequest,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """收集选中表的元数据"""
    try:
        service = TableMetadataService(db)
        result = await service.collect_and_save_table_metadata(
            current_user.id,
            request.database_config_id, 
            request.table_names
        )
        return result
    except Exception as e:
        logger.error(f"收集表元数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/")
async def get_table_metadata(
    database_config_id: int = None,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """获取表元数据列表"""
    try:
        service = TableMetadataService(db)
        metadata_list = service.get_user_table_metadata(
            current_user.id,
            database_config_id
        )

        data = [
            {
                "id": meta.id,
                "table_name": meta.table_name,
                "table_schema": meta.table_schema,
                "table_type": meta.table_type,
                "table_comment": meta.table_comment or "",
                "columns": meta.columns_info if meta.columns_info else [],
                "column_count": len(meta.columns_info) if meta.columns_info else 0,
                "row_count": meta.row_count,
                "is_enabled_for_qa": meta.is_enabled_for_qa,
                "qa_description": meta.qa_description or "",
                "business_context": meta.business_context or "",
                "created_at": meta.created_at.isoformat() if meta.created_at else "",
                "updated_at": meta.updated_at.isoformat() if meta.updated_at else "",
                "last_synced_at": meta.last_synced_at.isoformat() if meta.last_synced_at else "",
                "qa_settings": {
                    "is_enabled_for_qa": meta.is_enabled_for_qa,
                    "qa_description": meta.qa_description or "",
                    "business_context": meta.business_context or ""
                }
            }
            for meta in metadata_list
        ]
        
        return {
            "success": True,
            "data": data
        }
        
    except Exception as e:
        logger.error(f"获取表元数据失败: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }


@router.post("/by-table")
async def get_table_metadata_by_name(
    request: TableByNameRequest,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """根据表名获取表元数据"""
    try:
        service = TableMetadataService(db)
        metadata = service.get_table_metadata_by_name(
            current_user.id,
            request.database_config_id,
            request.table_name
        )
        
        if metadata:
            data = {
                "id": metadata.id,
                "table_name": metadata.table_name,
                "table_schema": metadata.table_schema,
                "table_type": metadata.table_type,
                "table_comment": metadata.table_comment or "",
                "columns": metadata.columns_info if metadata.columns_info else [],
                "column_count": len(metadata.columns_info) if metadata.columns_info else 0,
                "row_count": metadata.row_count,
                "is_enabled_for_qa": metadata.is_enabled_for_qa,
                "qa_description": metadata.qa_description or "",
                "business_context": metadata.business_context or "",
                "created_at": metadata.created_at.isoformat() if metadata.created_at else "",
                "updated_at": metadata.updated_at.isoformat() if metadata.updated_at else "",
                "last_synced_at": metadata.last_synced_at.isoformat() if metadata.last_synced_at else "",
                "qa_settings": {
                    "is_enabled_for_qa": metadata.is_enabled_for_qa,
                    "qa_description": metadata.qa_description or "",
                    "business_context": metadata.business_context or ""
                }
            }
            return {"success": True, "data": data}
        else:
            return {"success": False, "data": None, "message": "表元数据不存在"}
            
    except Exception as e:
        logger.error(f"获取表元数据失败: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }
        
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        logger.error(f"获取表元数据失败: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }


@router.put("/{metadata_id}/qa-settings")
async def update_qa_settings(
    metadata_id: int,
    settings: QASettingsUpdate,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """更新表的问答设置"""
    try:
        service = TableMetadataService(db)
        success = service.update_table_qa_settings(
            current_user.id,
            metadata_id, 
            settings.dict()
        )
        
        if success:
            return {"success": True, "message": "设置更新成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="表元数据不存在"
            )
    except Exception as e:
        logger.error(f"更新问答设置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


class TableSaveRequest(BaseModel):
    database_config_id: int = Field(..., description="数据库配置ID")
    table_names: List[str] = Field(..., description="要保存的表名列表")


@router.post("/save")
async def save_table_metadata(
    request: TableSaveRequest,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """保存选中表的元数据配置"""
    try:
        service = TableMetadataService(db)
        result = await service.save_table_metadata_config(
            user_id=current_user.id,
            database_config_id=request.database_config_id,
            table_names=request.table_names
        )
        
        logger.info(f"用户 {current_user.id} 保存了 {len(request.table_names)} 个表的配置")
        
        return {
            "success": True,
            "message": f"成功保存 {len(result['saved_tables'])} 个表的配置",
            "saved_tables": result['saved_tables'],
            "failed_tables": result.get('failed_tables', [])
        }
        
    except Exception as e:
        logger.error(f"保存表元数据配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存配置失败: {str(e)}"
        )