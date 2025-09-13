"""Excel file models for smart query."""

from sqlalchemy import Column, String, Integer, Text, Boolean, JSON, DateTime
from sqlalchemy.sql import func

from ..db.base import BaseModel


class ExcelFile(BaseModel):
    """Excel file model for storing file metadata."""
    
    __tablename__ = "excel_files"
    

    
    # Basic file information
    # user_id = Column(Integer, nullable=False)  # 用户ID
    original_filename = Column(String(255), nullable=False)  # 原始文件名
    file_path = Column(String(500), nullable=False)  # 文件存储路径
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    file_type = Column(String(50), nullable=False)  # 文件类型 (.xlsx, .xls, .csv)
    
    # Excel specific information
    sheet_names = Column(JSON, nullable=False)  # 所有sheet名称列表
    default_sheet = Column(String(100), nullable=True)  # 默认sheet名称
    
    # Data preview information
    columns_info = Column(JSON, nullable=False)  # 列信息：{sheet_name: [column_names]}
    preview_data = Column(JSON, nullable=False)  # 前5行数据：{sheet_name: [[row1], [row2], ...]}
    data_types = Column(JSON, nullable=True)  # 数据类型信息：{sheet_name: {column: dtype}}
    
    # Statistics
    total_rows = Column(JSON, nullable=True)  # 每个sheet的总行数：{sheet_name: row_count}
    total_columns = Column(JSON, nullable=True)  # 每个sheet的总列数：{sheet_name: column_count}
    
    # Processing status
    is_processed = Column(Boolean, default=True, nullable=False)  # 是否已处理
    processing_error = Column(Text, nullable=True)  # 处理错误信息
    
    # Upload information
    # upload_time = Column(DateTime, default=func.now(), nullable=False)  # 上传时间
    last_accessed = Column(DateTime, nullable=True)  # 最后访问时间
    
    def __repr__(self):
        return f"<ExcelFile(id={self.id}, filename='{self.original_filename}', user_id={self.user_id})>"
    
    @property
    def file_size_mb(self):
        """Get file size in MB."""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def sheet_count(self):
        """Get number of sheets."""
        return len(self.sheet_names) if self.sheet_names else 0
    
    def get_sheet_info(self, sheet_name: str = None):
        """Get information for a specific sheet or default sheet."""
        if not sheet_name:
            sheet_name = self.default_sheet or (self.sheet_names[0] if self.sheet_names else None)
        
        if not sheet_name or sheet_name not in self.sheet_names:
            return None
            
        return {
            'sheet_name': sheet_name,
            'columns': self.columns_info.get(sheet_name, []) if self.columns_info else [],
            'preview_data': self.preview_data.get(sheet_name, []) if self.preview_data else [],
            'data_types': self.data_types.get(sheet_name, {}) if self.data_types else {},
            'total_rows': self.total_rows.get(sheet_name, 0) if self.total_rows else 0,
            'total_columns': self.total_columns.get(sheet_name, 0) if self.total_columns else 0
        }
    
    def get_all_sheets_summary(self):
        """Get summary information for all sheets."""
        if not self.sheet_names:
            return []
            
        summary = []
        for sheet_name in self.sheet_names:
            sheet_info = self.get_sheet_info(sheet_name)
            if sheet_info:
                summary.append({
                    'sheet_name': sheet_name,
                    'columns_count': len(sheet_info['columns']),
                    'rows_count': sheet_info['total_rows'],
                    'columns': sheet_info['columns'][:10]  # 只显示前10列
                })
        return summary