"""Excel metadata extraction service."""

import os
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from ..models.excel_file import ExcelFile
from ..db.database import get_db
import logging

logger = logging.getLogger(__name__)


class ExcelMetadataService:
    """Service for extracting and managing Excel file metadata."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def extract_file_metadata(self, file_path: str, original_filename: str, 
                            user_id: int, file_size: int) -> Dict[str, Any]:
        """Extract metadata from Excel file."""
        try:
            # Determine file type
            file_extension = os.path.splitext(original_filename)[1].lower()
            
            # Read Excel file
            if file_extension == '.csv':
                # For CSV files, treat as single sheet
                df = pd.read_csv(file_path)
                sheets_data = {'Sheet1': df}
            else:
                # For Excel files, read all sheets
                sheets_data = pd.read_excel(file_path, sheet_name=None)
            
            # Extract metadata for each sheet
            sheet_names = list(sheets_data.keys())
            columns_info = {}
            preview_data = {}
            data_types = {}
            total_rows = {}
            total_columns = {}
            
            for sheet_name, df in sheets_data.items():
                # Clean column names (remove unnamed columns)
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                
                # Get column information - ensure proper encoding
                columns_info[sheet_name] = [str(col) if not isinstance(col, str) else col for col in df.columns.tolist()]
                
                # Get preview data (first 5 rows) and convert to JSON serializable format
                preview_df = df.head(5)
                # Convert all values to strings to ensure JSON serialization
                preview_values = []
                for row in preview_df.values:
                    string_row = []
                    for value in row:
                        if pd.isna(value):
                            string_row.append(None)
                        elif hasattr(value, 'strftime'):  # Handle datetime/timestamp objects
                            string_row.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                        else:
                            # Preserve Chinese characters and other unicode content
                            if isinstance(value, str):
                                string_row.append(value)
                            else:
                                string_row.append(str(value))
                    preview_values.append(string_row)
                preview_data[sheet_name] = preview_values
                
                # Get data types
                data_types[sheet_name] = {col: str(dtype) for col, dtype in df.dtypes.items()}
                
                # Get statistics
                total_rows[sheet_name] = len(df)
                total_columns[sheet_name] = len(df.columns)
            
            # Determine default sheet
            default_sheet = sheet_names[0] if sheet_names else None
            
            return {
                'sheet_names': sheet_names,
                'default_sheet': default_sheet,
                'columns_info': columns_info,
                'preview_data': preview_data,
                'data_types': data_types,
                'total_rows': total_rows,
                'total_columns': total_columns,
                'is_processed': True,
                'processing_error': None
            }
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            return {
                'sheet_names': [],
                'default_sheet': None,
                'columns_info': {},
                'preview_data': {},
                'data_types': {},
                'total_rows': {},
                'total_columns': {},
                'is_processed': False,
                'processing_error': str(e)
            }
    
    def save_file_metadata(self, file_path: str, original_filename: str, 
                          user_id: int, file_size: int) -> ExcelFile:
        """Extract and save Excel file metadata to database."""
        try:
            # Extract metadata
            metadata = self.extract_file_metadata(file_path, original_filename, user_id, file_size)
            
            # Determine file type
            file_extension = os.path.splitext(original_filename)[1].lower()
            
            # Create ExcelFile record
            excel_file = ExcelFile(
                user_id=user_id,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_extension,
                sheet_names=metadata['sheet_names'],
                default_sheet=metadata['default_sheet'],
                columns_info=metadata['columns_info'],
                preview_data=metadata['preview_data'],
                data_types=metadata['data_types'],
                total_rows=metadata['total_rows'],
                total_columns=metadata['total_columns'],
                is_processed=metadata['is_processed'],
                processing_error=metadata['processing_error']
            )
            
            # Save to database
            self.db.add(excel_file)
            self.db.commit()
            self.db.refresh(excel_file)
            
            logger.info(f"Saved metadata for file {original_filename} with ID {excel_file.id}")
            return excel_file
            
        except Exception as e:
            logger.error(f"Error saving metadata for {original_filename}: {str(e)}")
            self.db.rollback()
            raise
    
    def get_user_files(self, user_id: int, skip: int = 0, limit: int = 50) -> Tuple[List[ExcelFile], int]:
        """Get Excel files for a user with pagination."""
        try:
            # Get total count
            total = self.db.query(ExcelFile).filter(ExcelFile.user_id == user_id).count()
            
            # Get files with pagination
            files = (self.db.query(ExcelFile)
                    .filter(ExcelFile.user_id == user_id)
                    .order_by(ExcelFile.upload_time.desc())
                    .offset(skip)
                    .limit(limit)
                    .all())
            
            return files, total
            
        except Exception as e:
            logger.error(f"Error getting user files for user {user_id}: {str(e)}")
            return [], 0
    
    def get_file_by_id(self, file_id: int, user_id: int) -> Optional[ExcelFile]:
        """Get Excel file by ID and user ID."""
        try:
            return (self.db.query(ExcelFile)
                   .filter(ExcelFile.id == file_id, ExcelFile.user_id == user_id)
                   .first())
        except Exception as e:
            logger.error(f"Error getting file {file_id} for user {user_id}: {str(e)}")
            return None
    
    def delete_file(self, file_id: int, user_id: int) -> bool:
        """Delete Excel file record and physical file."""
        try:
            # Get file record
            excel_file = self.get_file_by_id(file_id, user_id)
            if not excel_file:
                return False
            
            # Delete physical file if exists
            if os.path.exists(excel_file.file_path):
                os.remove(excel_file.file_path)
                logger.info(f"Deleted physical file: {excel_file.file_path}")
            
            # Delete database record
            self.db.delete(excel_file)
            self.db.commit()
            
            logger.info(f"Deleted Excel file record with ID {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def update_last_accessed(self, file_id: int, user_id: int) -> bool:
        """Update last accessed time for a file."""
        try:
            excel_file = self.get_file_by_id(file_id, user_id)
            if not excel_file:
                return False
            
            from sqlalchemy.sql import func
            excel_file.last_accessed = func.now()
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating last accessed for file {file_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def get_file_summary_for_llm(self, user_id: int) -> List[Dict[str, Any]]:
        """Get file summary information for LLM context."""
        try:
            files = self.db.query(ExcelFile).filter(ExcelFile.user_id == user_id).all()
            
            summary = []
            for file in files:
                file_info = {
                    'file_id': file.id,
                    'filename': file.original_filename,
                    'file_type': file.file_type,
                    'sheets': file.get_all_sheets_summary(),
                    'upload_time': file.upload_time.isoformat() if file.upload_time else None
                }
                summary.append(file_info)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting file summary for user {user_id}: {str(e)}")
            return []