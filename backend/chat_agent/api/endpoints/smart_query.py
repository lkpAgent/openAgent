from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import pandas as pd
import io
import json
import os
import tempfile
from datetime import datetime

from chat_agent.db.database import get_db
from chat_agent.services.auth import AuthService
from chat_agent.utils.schemas import BaseResponse
from chat_agent.services.smart_query import (
    SmartQueryService,
    ExcelAnalysisService,
    DatabaseQueryService
)
from pydantic import BaseModel

router = APIRouter(prefix="/smart-query", tags=["smart-query"])
security = HTTPBearer()

# Request/Response Models
class DatabaseConfig(BaseModel):
    type: str
    host: str
    port: str
    database: str
    username: str
    password: str

class QueryRequest(BaseModel):
    query: str
    page: int = 1
    page_size: int = 20
    table_name: Optional[str] = None

class TableSchemaRequest(BaseModel):
    table_name: str

class ExcelUploadResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

@router.post("/upload-excel", response_model=ExcelUploadResponse)
async def upload_excel(
    file: UploadFile = File(...),
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传Excel文件并进行预处理
    """
    try:
        # 验证文件类型
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件格式，请上传 .xlsx, .xls 或 .csv 文件"
            )
        
        # 验证文件大小 (10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小不能超过 10MB"
            )
        
        # 读取文件内容
        try:
            if file_extension == '.csv':
                df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            else:
                df = pd.read_excel(io.BytesIO(content))
        except UnicodeDecodeError:
            # 尝试其他编码
            if file_extension == '.csv':
                df = pd.read_csv(io.BytesIO(content), encoding='gbk')
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="文件编码错误，请确保文件为UTF-8或GBK编码"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件读取失败: {str(e)}"
            )
        
        # 数据预处理和分析
        excel_service = ExcelAnalysisService()
        analysis_result = excel_service.analyze_dataframe(df, file.filename)
        
        # 保存文件到临时目录（用于后续查询）
        temp_dir = tempfile.gettempdir()
        temp_filename = f"excel_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        temp_path = os.path.join(temp_dir, temp_filename)
        df.to_pickle(temp_path)
        
        # 将文件路径保存到分析结果中
        analysis_result['temp_file_path'] = temp_path
        
        return ExcelUploadResponse(
            success=True,
            message="Excel文件上传成功",
            data=analysis_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件处理失败: {str(e)}"
        )

@router.post("/test-db-connection", response_model=BaseResponse)
async def test_database_connection(
    config: DatabaseConfig,
    current_user = Depends(AuthService.get_current_user)
):
    """
    测试数据库连接
    """
    try:
        db_service = DatabaseQueryService()
        is_connected = await db_service.test_connection(config.dict())
        
        if is_connected:
            return BaseResponse(
                success=True,
                message="数据库连接测试成功"
            )
        else:
            return BaseResponse(
                success=False,
                message="数据库连接测试失败"
            )
            
    except Exception as e:
        return BaseResponse(
            success=False,
            message=f"连接测试失败: {str(e)}"
        )

@router.post("/connect-database", response_model=QueryResponse)
async def connect_database(
    config: DatabaseConfig,
    current_user = Depends(AuthService.get_current_user)
):
    """
    连接数据库并获取表列表
    """
    try:
        db_service = DatabaseQueryService()
        connection_result = await db_service.connect_database(config.dict(), current_user.id)
        
        if connection_result['success']:
            return QueryResponse(
                success=True,
                message="数据库连接成功",
                data=connection_result['data']
            )
        else:
            return QueryResponse(
                success=False,
                message=connection_result['message']
            )
            
    except Exception as e:
        return QueryResponse(
            success=False,
            message=f"数据库连接失败: {str(e)}"
        )

@router.post("/table-schema", response_model=QueryResponse)
async def get_table_schema(
    request: TableSchemaRequest,
    current_user = Depends(AuthService.get_current_user)
):
    """
    获取数据表结构
    """
    try:
        db_service = DatabaseQueryService()
        schema_result = await db_service.get_table_schema(request.table_name, current_user.id)
        
        if schema_result['success']:
            return QueryResponse(
                success=True,
                message="获取表结构成功",
                data=schema_result['data']
            )
        else:
            return QueryResponse(
                success=False,
                message=schema_result['message']
            )
            
    except Exception as e:
        return QueryResponse(
            success=False,
            message=f"获取表结构失败: {str(e)}"
        )

@router.post("/execute-excel-query", response_model=QueryResponse)
async def execute_excel_query(
    request: QueryRequest,
    current_user = Depends(AuthService.get_current_user)
):
    """
    执行Excel数据查询
    """
    try:
        excel_service = ExcelAnalysisService()
        query_result = await excel_service.execute_natural_language_query(
            request.query,
            current_user.id,
            page=request.page,
            page_size=request.page_size
        )
        
        if query_result['success']:
            return QueryResponse(
                success=True,
                message="Excel查询执行成功",
                data=query_result['data']
            )
        else:
            return QueryResponse(
                success=False,
                message=query_result['message']
            )
            
    except Exception as e:
        return QueryResponse(
            success=False,
            message=f"Excel查询执行失败: {str(e)}"
        )

@router.post("/execute-db-query", response_model=QueryResponse)
async def execute_database_query(
    request: QueryRequest,
    current_user = Depends(AuthService.get_current_user)
):
    """
    执行数据库查询
    """
    try:
        if not request.table_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="数据库查询需要指定表名"
            )
        
        db_service = DatabaseQueryService()
        query_result = await db_service.execute_natural_language_query(
            request.query,
            request.table_name,
            current_user.id,
            page=request.page,
            page_size=request.page_size
        )
        
        if query_result['success']:
            return QueryResponse(
                success=True,
                message="数据库查询执行成功",
                data=query_result['data']
            )
        else:
            return QueryResponse(
                success=False,
                message=query_result['message']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        return QueryResponse(
            success=False,
            message=f"数据库查询执行失败: {str(e)}"
        )

@router.delete("/cleanup-temp-files")
async def cleanup_temp_files(
    current_user = Depends(AuthService.get_current_user)
):
    """
    清理临时文件
    """
    try:
        temp_dir = tempfile.gettempdir()
        user_prefix = f"excel_{current_user.id}_"
        
        cleaned_count = 0
        for filename in os.listdir(temp_dir):
            if filename.startswith(user_prefix) and filename.endswith('.pkl'):
                file_path = os.path.join(temp_dir, filename)
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                except OSError:
                    pass
        
        return BaseResponse(
            success=True,
            message=f"已清理 {cleaned_count} 个临时文件"
        )
        
    except Exception as e:
        return BaseResponse(
            success=False,
            message=f"清理临时文件失败: {str(e)}"
        )