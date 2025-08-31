"""File storage service supporting local and S3 storage."""

import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, BinaryIO, Dict, Any
from fastapi import UploadFile
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..core.config import settings
from ..utils.file_utils import FileUtils


class StorageBackend(ABC):
    """Abstract storage backend interface."""
    
    @abstractmethod
    async def upload_file(
        self, 
        file: UploadFile, 
        file_path: str
    ) -> Dict[str, Any]:
        """Upload file and return storage info."""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage."""
        pass
    
    @abstractmethod
    async def get_file_url(self, file_path: str) -> Optional[str]:
        """Get file access URL."""
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        pass


class LocalStorageBackend(StorageBackend):
    """Local file system storage backend."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(
        self, 
        file: UploadFile, 
        file_path: str
    ) -> Dict[str, Any]:
        """Upload file to local storage."""
        full_path = self.base_path / file_path
        
        # Create directory if it doesn't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(full_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Get file info
        file_info = FileUtils.get_file_info(str(full_path))
        
        return {
            "file_path": file_path,
            "full_path": str(full_path),
            "size": file_info["size_bytes"],
            "mime_type": file_info["mime_type"],
            "storage_type": "local"
        }
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage."""
        full_path = self.base_path / file_path
        return FileUtils.delete_file(str(full_path))
    
    async def get_file_url(self, file_path: str) -> Optional[str]:
        """Get local file URL (for development)."""
        # In production, you might want to serve files through a web server
        full_path = self.base_path / file_path
        if full_path.exists():
            return f"/files/{file_path}"
        return None
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in local storage."""
        full_path = self.base_path / file_path
        return full_path.exists()


class S3StorageBackend(StorageBackend):
    """Amazon S3 storage backend."""
    
    def __init__(
        self, 
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: str = "us-east-1",
        endpoint_url: Optional[str] = None
    ):
        self.bucket_name = bucket_name
        self.aws_region = aws_region
        
        # Initialize S3 client
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        self.s3_client = session.client(
            's3',
            endpoint_url=endpoint_url  # For S3-compatible services like MinIO
        )
        
        # Verify bucket exists or create it
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure S3 bucket exists."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                # Bucket doesn't exist, create it
                try:
                    if self.aws_region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.aws_region}
                        )
                except ClientError as create_error:
                    raise Exception(f"Failed to create S3 bucket: {create_error}")
            else:
                raise Exception(f"Failed to access S3 bucket: {e}")
    
    async def upload_file(
        self, 
        file: UploadFile, 
        file_path: str
    ) -> Dict[str, Any]:
        """Upload file to S3."""
        try:
            # Read file content
            content = await file.read()
            
            # Determine content type
            content_type = FileUtils.get_mime_type(file.filename) or 'application/octet-stream'
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=content,
                ContentType=content_type,
                Metadata={
                    'original_filename': file.filename or 'unknown',
                    'upload_timestamp': str(int(os.time.time()))
                }
            )
            
            return {
                "file_path": file_path,
                "bucket": self.bucket_name,
                "size": len(content),
                "mime_type": content_type,
                "storage_type": "s3"
            }
        except (ClientError, NoCredentialsError) as e:
            raise Exception(f"Failed to upload file to S3: {e}")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return True
        except ClientError:
            return False
    
    async def get_file_url(self, file_path: str) -> Optional[str]:
        """Get presigned URL for S3 file."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_path},
                ExpiresIn=3600  # 1 hour
            )
            return url
        except ClientError:
            return None
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return True
        except ClientError:
            return False


class StorageService:
    """统一的存储服务管理器"""
    
    def __init__(self):
        self.storage_type = settings.storage.storage_type
        
        if self.storage_type == 's3':
            self.backend = S3StorageBackend(
                bucket_name=settings.storage.s3_bucket_name,
                aws_access_key_id=settings.storage.aws_access_key_id,
                aws_secret_access_key=settings.storage.aws_secret_access_key,
                aws_region=settings.storage.aws_region,
                endpoint_url=settings.storage.s3_endpoint_url
            )
        else:
            self.backend = LocalStorageBackend(settings.storage.upload_directory)
    
    def generate_file_path(self, knowledge_base_id: int, filename: str) -> str:
        """Generate unique file path for storage."""
        # Sanitize filename
        safe_filename = FileUtils.sanitize_filename(filename)
        
        # Generate unique identifier
        file_id = str(uuid.uuid4())
        
        # Create path: kb_{id}/{file_id}_{filename}
        return f"kb_{knowledge_base_id}/{file_id}_{safe_filename}"
    
    async def upload_file(
        self, 
        file: UploadFile, 
        knowledge_base_id: int
    ) -> Dict[str, Any]:
        """Upload file using configured storage backend."""
        file_path = self.generate_file_path(knowledge_base_id, file.filename)
        return await self.backend.upload_file(file, file_path)
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file using configured storage backend."""
        return await self.backend.delete_file(file_path)
    
    async def get_file_url(self, file_path: str) -> Optional[str]:
        """Get file access URL."""
        return await self.backend.get_file_url(file_path)
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        return await self.backend.file_exists(file_path)


# Global storage service instance
storage_service = StorageService()