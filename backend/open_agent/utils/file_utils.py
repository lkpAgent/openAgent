"""File utilities."""

import os
import re
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, List, Dict, Any


class FileUtils:
    """Utility class for file operations."""
    
    # Allowed file extensions for document upload
    ALLOWED_EXTENSIONS = {
        '.txt', '.md', '.csv',  # Text files
        '.pdf',  # PDF files
        '.docx', '.doc',  # Word documents
        '.xlsx', '.xls',  # Excel files
        '.pptx', '.ppt',  # PowerPoint files
        '.rtf',  # Rich text format
        '.odt', '.ods', '.odp'  # OpenDocument formats
    }
    
    # MIME type mappings
    MIME_TYPE_MAPPING = {
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.csv': 'text/csv',
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.rtf': 'application/rtf',
        '.odt': 'application/vnd.oasis.opendocument.text',
        '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
        '.odp': 'application/vnd.oasis.opendocument.presentation'
    }
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to remove dangerous characters."""
        # Remove or replace dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        
        # Ensure filename is not empty
        if not filename:
            filename = 'unnamed_file'
        
        # Limit filename length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = 'md5') -> str:
        """Calculate file hash."""
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = path.stat()
        
        # Get MIME type
        mime_type, encoding = mimetypes.guess_type(str(path))
        
        return {
            'filename': path.name,
            'extension': path.suffix.lower(),
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'mime_type': mime_type,
            'encoding': encoding,
            'created_at': stat.st_ctime,
            'modified_at': stat.st_mtime,
            'is_file': path.is_file(),
            'is_readable': os.access(path, os.R_OK)
        }
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: Optional[List[str]] = None) -> bool:
        """Validate file extension."""
        if allowed_extensions is None:
            allowed_extensions = list(FileUtils.ALLOWED_EXTENSIONS)
        
        extension = Path(filename).suffix.lower()
        return extension in allowed_extensions
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int) -> bool:
        """Validate file size."""
        return file_size <= max_size
    
    @staticmethod
    def create_directory(directory_path: str) -> bool:
        """Create directory if it doesn't exist."""
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Safely delete a file."""
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_mime_type(filename: str) -> Optional[str]:
        """Get MIME type for filename."""
        extension = Path(filename).suffix.lower()
        return FileUtils.MIME_TYPE_MAPPING.get(extension)
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    @staticmethod
    def is_text_file(filename: str) -> bool:
        """Check if file is a text file."""
        extension = Path(filename).suffix.lower()
        return extension in {'.txt', '.md', '.csv', '.rtf'}
    
    @staticmethod
    def is_pdf_file(filename: str) -> bool:
        """Check if file is a PDF."""
        extension = Path(filename).suffix.lower()
        return extension == '.pdf'
    
    @staticmethod
    def is_office_file(filename: str) -> bool:
        """Check if file is an Office document."""
        extension = Path(filename).suffix.lower()
        return extension in {'.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.odt', '.ods', '.odp'}
    
    @staticmethod
    def get_file_category(filename: str) -> str:
        """Get file category based on extension."""
        extension = Path(filename).suffix.lower()
        
        if extension in {'.txt', '.md', '.csv', '.rtf'}:
            return 'text'
        elif extension == '.pdf':
            return 'pdf'
        elif extension in {'.docx', '.doc', '.odt'}:
            return 'document'
        elif extension in {'.xlsx', '.xls', '.ods'}:
            return 'spreadsheet'
        elif extension in {'.pptx', '.ppt', '.odp'}:
            return 'presentation'
        else:
            return 'unknown'