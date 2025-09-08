"""数据库配置服务"""

import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from cryptography.fernet import Fernet
import base64
import os

from ..models.database_config import DatabaseConfig
from ..utils.logger import get_logger
from ..utils.exceptions import ValidationError, NotFoundError
from .postgresql_tool_manager import get_postgresql_tool

logger = get_logger("database_config_service")


class DatabaseConfigService:
    """数据库配置管理服务"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.postgresql_tool = get_postgresql_tool()
        # 初始化加密密钥
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
    def _get_or_create_encryption_key(self) -> bytes:
        """获取或创建加密密钥"""
        key_file = "db_config_key.key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _encrypt_password(self, password: str) -> str:
        """加密密码"""
        return self.cipher.encrypt(password.encode()).decode()
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """解密密码"""
        return self.cipher.decrypt(encrypted_password.encode()).decode()
    
    async def create_config(self, user_id: int, config_data: Dict[str, Any]) -> DatabaseConfig:
        """创建数据库配置"""
        try:
            # 验证配置
            required_fields = ['name', 'db_type', 'host', 'port', 'database', 'username', 'password']
            for field in required_fields:
                if field not in config_data:
                    raise ValidationError(f"缺少必需字段: {field}")
            
            # 测试连接
            test_config = {
                'host': config_data['host'],
                'port': config_data['port'],
                'database': config_data['database'],
                'username': config_data['username'],
                'password': config_data['password']
            }
            
            test_result = await self.postgresql_tool.execute(
                operation="test_connection",
                connection_config=test_config
            )
            
            if not test_result.success:
                raise ValidationError(f"数据库连接测试失败: {test_result.error}")
            
            # 如果设置为默认配置，先取消其他默认配置
            if config_data.get('is_default', False):
                self.db.query(DatabaseConfig).filter(
                    and_(DatabaseConfig.created_by == user_id, DatabaseConfig.is_default == True)
                ).update({'is_default': False})
            
            # 创建配置
            db_config = DatabaseConfig(
                created_by=user_id,
                name=config_data['name'],
                db_type=config_data['db_type'],
                host=config_data['host'],
                port=config_data['port'],
                database=config_data['database'],
                username=config_data['username'],
                password=self._encrypt_password(config_data['password']),
                is_active=config_data.get('is_active', True),
                is_default=config_data.get('is_default', False),
                connection_params=config_data.get('connection_params')
            )
            
            self.db.add(db_config)
            self.db.commit()
            self.db.refresh(db_config)
            
            logger.info(f"创建数据库配置成功: {db_config.name} (ID: {db_config.id})")
            return db_config
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建数据库配置失败: {str(e)}")
            raise
    
    def get_user_configs(self, user_id: int, active_only: bool = True) -> List[DatabaseConfig]:
        """获取用户的数据库配置列表"""
        query = self.db.query(DatabaseConfig).filter(DatabaseConfig.created_by == user_id)
        if active_only:
            query = query.filter(DatabaseConfig.is_active == True)
        return query.order_by(DatabaseConfig.created_at.desc()).all()
    
    def get_config_by_id(self, config_id: int, user_id: int) -> Optional[DatabaseConfig]:
        """根据ID获取配置"""
        return self.db.query(DatabaseConfig).filter(
            and_(DatabaseConfig.id == config_id, DatabaseConfig.created_by == user_id)
        ).first()
    
    def get_default_config(self, user_id: int) -> Optional[DatabaseConfig]:
        """获取用户的默认配置"""
        return self.db.query(DatabaseConfig).filter(
            and_(
                DatabaseConfig.created_by == user_id,
                # DatabaseConfig.is_default == True,
                DatabaseConfig.is_active == True
            )
        ).first()
    
    async def test_connection(self, config_id: int, user_id: int) -> Dict[str, Any]:
        """测试数据库连接"""
        config = self.get_config_by_id(config_id, user_id)
        if not config:
            raise NotFoundError("数据库配置不存在")
        
        test_config = {
            'host': config.host,
            'port': config.port,
            'database': config.database,
            'username': config.username,
            'password': self._decrypt_password(config.password)
        }
        
        result = await self.postgresql_tool.execute(
            operation="test_connection",
            connection_config=test_config
        )
        
        return {
            'success': result.success,
            'message': result.result.get('message') if result.success else result.error,
            'details': result.result if result.success else None
        }
    
    async def connect_and_get_tables(self, config_id: int, user_id: int) -> Dict[str, Any]:
        """连接数据库并获取表列表"""
        config = self.get_config_by_id(config_id, user_id)
        if not config:
            raise NotFoundError("数据库配置不存在")
        
        connection_config = {
            'host': config.host,
            'port': config.port,
            'database': config.database,
            'username': config.username,
            'password': self._decrypt_password(config.password)
        }
        
        # 连接数据库
        connect_result = await self.postgresql_tool.execute(
            operation="connect",
            connection_config=connection_config,
            user_id=str(user_id)
        )
        
        if not connect_result.success:
            return {
                'success': False,
                'message': connect_result.error
            }
            # 连接信息已保存到PostgreSQLMCPTool的connections中
        return {
            'success': True,
            'data': connect_result.result,
            'config_name': config.name
        }
    
    async def get_table_data(self, table_name: str, user_id: int, limit: int = 100) -> Dict[str, Any]:
        """获取表数据预览（复用已建立的连接）"""
        try:
            # 检查是否已有连接
            if str(user_id) not in self.postgresql_tool.connections:
                return {
                    'success': False,
                    'message': '数据库连接已断开，请重新连接数据库'
                }
            
            # 直接使用已建立的连接执行查询
            sql_query = f"SELECT * FROM {table_name}"
            result = await self.postgresql_tool.execute(
                operation="execute_query",
                user_id=str(user_id),
                sql_query=sql_query,
                limit=limit
            )
            
            if not result.success:
                return {
                    'success': False,
                    'message': result.error
                }
            
            return {
                'success': True,
                'data': result.result
            }
            
        except Exception as e:
            logger.error(f"获取表数据失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'获取表数据失败: {str(e)}'
            }
    
    def disconnect_database(self, user_id: int) -> Dict[str, Any]:
        """断开数据库连接"""
        try:
            # 从PostgreSQLMCPTool断开连接
            self.postgresql_tool.execute(
                operation="disconnect",
                user_id=str(user_id)
            )
            
            # 从本地连接管理中移除
            if user_id in self.user_connections:
                del self.user_connections[user_id]
            
            return {
                'success': True,
                'message': '数据库连接已断开'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'断开连接失败: {str(e)}'
            }
    
    def get_config_by_type(self, user_id: int, db_type: str) -> Optional[DatabaseConfig]:
        """根据数据库类型获取用户配置"""
        return self.db.query(DatabaseConfig).filter(
            and_(
                DatabaseConfig.created_by == user_id,
                DatabaseConfig.db_type == db_type,
                DatabaseConfig.is_active == True
            )
        ).first()
    
    async def create_or_update_config(self, user_id: int, config_data: Dict[str, Any]) -> DatabaseConfig:
        """创建或更新数据库配置（保证db_type唯一性）"""
        try:
            # 检查是否已存在该类型的配置
            existing_config = self.get_config_by_type(user_id, config_data['db_type'])
            
            if existing_config:
                # 更新现有配置
                for key, value in config_data.items():
                    if key == 'password':
                        setattr(existing_config, key, self._encrypt_password(value))
                    elif hasattr(existing_config, key):
                        setattr(existing_config, key, value)
                
                self.db.commit()
                self.db.refresh(existing_config)
                logger.info(f"更新数据库配置成功: {existing_config.name} (ID: {existing_config.id})")
                return existing_config
            else:
                # 创建新配置
                return await self.create_config(user_id, config_data)
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建或更新数据库配置失败: {str(e)}")
            raise