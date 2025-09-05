from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import pandas as pd
import io
import json
import os
import tempfile
import logging
from datetime import datetime

from chat_agent.db.database import get_db
from chat_agent.services.auth import AuthService
from chat_agent.utils.schemas import BaseResponse
from chat_agent.services.smart_query import (
    SmartQueryService,
    ExcelAnalysisService,
    DatabaseQueryService
)
from chat_agent.services.excel_metadata_service import ExcelMetadataService
from pydantic import BaseModel
import uuid
from pathlib import Path
from chat_agent.utils.file_utils import FileUtils

logger = logging.getLogger(__name__)

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
    file_id: int
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None  # 添加data字段


class QueryResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# 通用返回结构
class NormalResponse(BaseModel):
    success: bool
    message: str

class ExcelPreviewRequest(BaseModel):
    file_id: str
    page: int = 1
    page_size: int = 20

class FileListResponse(BaseModel):
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
        file_size = len(content)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小不能超过 10MB"
            )
        
        # 创建持久化目录结构
        backend_dir = Path(__file__).parent.parent.parent.parent  # 获取backend目录
        data_dir = backend_dir / "data/uploads"
        excel_user_dir = data_dir / f"excel_{current_user.id}"
        
        # 确保目录存在
        excel_user_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名：{uuid}_{原始文件名称}
        file_id = str(uuid.uuid4())
        safe_filename = FileUtils.sanitize_filename(file.filename)
        new_filename = f"{file_id}_{safe_filename}"
        file_path = excel_user_dir / new_filename
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 使用Excel元信息服务提取并保存元信息
        metadata_service = ExcelMetadataService(db)
        excel_file = metadata_service.save_file_metadata(
            file_path=str(file_path),
            original_filename=file.filename,
            user_id=current_user.id,
            file_size=file_size
        )
        
        # 为了兼容现有前端，仍然创建pickle文件
        try:
            if file_extension == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                df = pd.read_excel(file_path)
        except UnicodeDecodeError:
            if file_extension == '.csv':
                df = pd.read_csv(file_path, encoding='gbk')
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
        
        # 保存pickle文件到同一目录
        pickle_filename = f"{file_id}_{safe_filename}.pkl"
        pickle_path = excel_user_dir / pickle_filename
        df.to_pickle(pickle_path)
        
        # 数据预处理和分析（保持兼容性）
        excel_service = ExcelAnalysisService()
        analysis_result = excel_service.analyze_dataframe(df, file.filename)
        
        # 添加数据库文件信息
        analysis_result.update({
            'file_id': str(excel_file.id),
            'database_id': excel_file.id,
            'temp_file_path': str(pickle_path),  # 更新为新的pickle路径
            'original_filename': file.filename,
            'file_size_mb': excel_file.file_size_mb,
            'sheet_names': excel_file.sheet_names,
            'upload_time': excel_file.upload_time.isoformat() if excel_file.upload_time else None
        })
        
        return ExcelUploadResponse(
            file_id=excel_file.id,
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

@router.post("/preview-excel", response_model=QueryResponse)
async def preview_excel(
    request: ExcelPreviewRequest,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    预览Excel文件数据
    """
    try:
        logger.info(f"Preview request for file_id: {request.file_id}, user: {current_user.id}")
        
        # 验证file_id格式
        try:
            file_id = int(request.file_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"无效的文件ID格式: {request.file_id}"
            )
        
        # 从数据库获取文件信息
        metadata_service = ExcelMetadataService(db)
        excel_file = metadata_service.get_file_by_id(file_id, current_user.id)
        
        if not excel_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在或已被删除"
            )
        
        # 检查文件是否存在
        if not os.path.exists(excel_file.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件已被移动或删除"
            )
        
        # 更新最后访问时间
        metadata_service.update_last_accessed(file_id, current_user.id)
        
        # 读取Excel文件
        if excel_file.file_type.lower() == 'csv':
            df = pd.read_csv(excel_file.file_path, encoding='utf-8')
        else:
            # 对于Excel文件，使用默认sheet或第一个sheet
            sheet_name = excel_file.default_sheet if excel_file.default_sheet else 0
            df = pd.read_excel(excel_file.file_path, sheet_name=sheet_name)
        
        # 计算分页
        total_rows = len(df)
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        
        # 获取分页数据
        paginated_df = df.iloc[start_idx:end_idx]
        
        # 转换为字典格式
        data = paginated_df.fillna('').to_dict('records')
        columns = df.columns.tolist()
        
        return QueryResponse(
            success=True,
            message="Excel文件预览加载成功",
            data={
                'data': data,
                'columns': columns,
                'total_rows': total_rows,
                'page': request.page,
                'page_size': request.page_size,
                'total_pages': (total_rows + request.page_size - 1) // request.page_size
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览文件失败: {str(e)}"
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

@router.get("/files", response_model=FileListResponse)
async def get_file_list(
    page: int = 1,
    page_size: int = 20,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户上传的Excel文件列表
    """
    try:
        metadata_service = ExcelMetadataService(db)
        skip = (page - 1) * page_size
        files, total = metadata_service.get_user_files(current_user.id, skip, page_size)
        
        file_list = []
        for file in files:
            file_info = {
                'id': file.id,
                'filename': file.original_filename,
                'file_size': file.file_size,
                'file_size_mb': file.file_size_mb,
                'file_type': file.file_type,
                'sheet_names': file.sheet_names,
                'sheet_count': file.sheet_count,
                'upload_time': file.upload_time.isoformat() if file.upload_time else None,
                'last_accessed': file.last_accessed.isoformat() if file.last_accessed else None,
                'is_processed': file.is_processed,
                'processing_error': file.processing_error
            }
            file_list.append(file_info)
        
        return FileListResponse(
            success=True,
            message="获取文件列表成功",
            data={
                'files': file_list,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        )
        
    except Exception as e:
        return FileListResponse(
            success=False,
            message=f"获取文件列表失败: {str(e)}"
        )

@router.delete("/files/{file_id}", response_model=NormalResponse)
async def delete_file(
    file_id: int,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除指定的Excel文件
    """
    try:
        metadata_service = ExcelMetadataService(db)
        success = metadata_service.delete_file(file_id, current_user.id)
        
        if success:
            return NormalResponse(
                success=True,
                message="文件删除成功"
            )
        else:
            return NormalResponse(
                success=False,
                message="文件不存在或删除失败"
            )
            
    except Exception as e:
        return NormalResponse(
            success=True,
            message=str(e)
        )

@router.get("/files/{file_id}/info", response_model=QueryResponse)
async def get_file_info(
    file_id: int,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定文件的详细信息
    """
    try:
        metadata_service = ExcelMetadataService(db)
        excel_file = metadata_service.get_file_by_id(file_id, current_user.id)
        
        if not excel_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 更新最后访问时间
        metadata_service.update_last_accessed(file_id, current_user.id)
        
        file_info = {
            'id': excel_file.id,
            'filename': excel_file.original_filename,
            'file_size': excel_file.file_size,
            'file_size_mb': excel_file.file_size_mb,
            'file_type': excel_file.file_type,
            'sheet_names': excel_file.sheet_names,
            'default_sheet': excel_file.default_sheet,
            'columns_info': excel_file.columns_info,
            'preview_data': excel_file.preview_data,
            'data_types': excel_file.data_types,
            'total_rows': excel_file.total_rows,
            'total_columns': excel_file.total_columns,
            'upload_time': excel_file.upload_time.isoformat() if excel_file.upload_time else None,
            'last_accessed': excel_file.last_accessed.isoformat() if excel_file.last_accessed else None,
            'sheets_summary': excel_file.get_all_sheets_summary()
        }
        
        return QueryResponse(
            success=True,
            message="获取文件信息成功",
            data=file_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return QueryResponse(
            success=False,
            message=f"获取文件信息失败: {str(e)}"
        )