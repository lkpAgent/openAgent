"""表元数据管理服务"""

import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime

from ..models.table_metadata import TableMetadata
from ..models.database_config import DatabaseConfig
from ..utils.logger import get_logger
from ..utils.exceptions import ValidationError, NotFoundError
from .postgresql_tool_manager import get_postgresql_tool

logger = get_logger("table_metadata_service")


class TableMetadataService:
    """表元数据管理服务"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.postgresql_tool = get_postgresql_tool()
    
    async def collect_and_save_table_metadata(
        self, 
        user_id: int, 
        database_config_id: int, 
        table_names: List[str]
    ) -> Dict[str, Any]:
        """收集并保存表元数据"""
        try:
            # 获取数据库配置
            db_config = self.db.query(DatabaseConfig).filter(
                and_(DatabaseConfig.id == database_config_id, DatabaseConfig.created_by == user_id)
            ).first()
            
            if not db_config:
                raise NotFoundError("数据库配置不存在")
            
            # 检查是否已有连接，如果没有则建立连接
            user_id_str = str(user_id)
            if user_id_str not in self.postgresql_tool.connections:
                connection_config = {
                    'host': db_config.host,
                    'port': db_config.port,
                    'database': db_config.database,
                    'username': db_config.username,
                    'password': self._decrypt_password(db_config.password)
                }
                
                # 连接数据库
                connect_result = await self.postgresql_tool.execute(
                    operation="connect",
                    connection_config=connection_config,
                    user_id=user_id_str
                )
                
                if not connect_result.success:
                    raise Exception(f"数据库连接失败: {connect_result.error}")
                
                logger.info(f"为用户 {user_id} 建立了新的数据库连接")
            else:
                logger.info(f"复用用户 {user_id} 的现有数据库连接")
            
            collected_tables = []
            failed_tables = []
            
            for table_name in table_names:
                try:
                    # 收集表元数据
                    metadata = await self._collect_single_table_metadata(
                        user_id, table_name
                    )
                    
                    # 保存或更新元数据
                    table_metadata = await self._save_table_metadata(
                        user_id, database_config_id, table_name, metadata
                    )
                    
                    collected_tables.append({
                        'table_name': table_name,
                        'metadata_id': table_metadata.id,
                        'columns_count': len(metadata['columns_info']),
                        'sample_rows': len(metadata['sample_data'])
                    })
                    
                except Exception as e:
                    print(e)
                    logger.error(f"收集表 {table_name} 元数据失败: {str(e)}")
                    failed_tables.append({
                        'table_name': table_name,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'collected_tables': collected_tables,
                'failed_tables': failed_tables,
                'total_collected': len(collected_tables),
                'total_failed': len(failed_tables)
            }
            
        except Exception as e:
            logger.error(f"收集表元数据失败: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    async def _collect_single_table_metadata(
        self, 
        user_id: int, 
        table_name: str
    ) -> Dict[str, Any]:
        """收集单个表的元数据"""
        
        # 获取表结构
        schema_result = await self.postgresql_tool.execute(
            operation="describe_table",
            user_id=str(user_id),
            table_name=table_name
        )
        
        if not schema_result.success:
            raise Exception(f"获取表结构失败: {schema_result.error}")
        
        schema_data = schema_result.result
        
        # 获取示例数据（前5条）
        sample_result = await self.postgresql_tool.execute(
            operation="execute_query",
            user_id=str(user_id),
            sql_query=f"SELECT * FROM {table_name} LIMIT 5",
            limit=5
        )
        
        sample_data = []
        if sample_result.success:
            sample_data = sample_result.result.get('data', [])
        
        # 获取行数统计
        count_result = await self.postgresql_tool.execute(
            operation="execute_query",
            user_id=str(user_id),
            sql_query=f"SELECT COUNT(*) as total_rows FROM {table_name}",
            limit=1
        )
        
        row_count = 0
        if count_result.success and count_result.result.get('data'):
            row_count = count_result.result['data'][0].get('total_rows', 0)
        
        return {
            'columns_info': schema_data.get('columns', []),
            'primary_keys': schema_data.get('primary_keys', []),
            'foreign_keys': schema_data.get('foreign_keys', []),
            'indexes': schema_data.get('indexes', []),
            'sample_data': sample_data,
            'row_count': row_count,
            'table_comment': schema_data.get('table_comment', '')
        }
    
    async def _save_table_metadata(
        self, 
        user_id: int, 
        database_config_id: int, 
        table_name: str, 
        metadata: Dict[str, Any]
    ) -> TableMetadata:
        """保存表元数据"""
        
        # 检查是否已存在
        existing = self.db.query(TableMetadata).filter(
            and_(
                TableMetadata.created_by == user_id,
                TableMetadata.database_config_id == database_config_id,
                TableMetadata.table_name == table_name
            )
        ).first()
        
        if existing:
            # 更新现有记录
            existing.columns_info = metadata['columns_info']
            existing.primary_keys = metadata['primary_keys']
            existing.foreign_keys = metadata['foreign_keys']
            existing.indexes = metadata['indexes']
            existing.sample_data = metadata['sample_data']
            existing.row_count = metadata['row_count']
            existing.table_comment = metadata['table_comment']
            existing.last_synced_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # 创建新记录
            table_metadata = TableMetadata(
                created_by=user_id,
                database_config_id=database_config_id,
                table_name=table_name,
                table_schema='public',
                table_type='BASE TABLE',
                table_comment=metadata['table_comment'],
                columns_info=metadata['columns_info'],
                primary_keys=metadata['primary_keys'],
                foreign_keys=metadata['foreign_keys'],
                indexes=metadata['indexes'],
                sample_data=metadata['sample_data'],
                row_count=metadata['row_count'],
                is_enabled_for_qa=True,
                last_synced_at=datetime.utcnow()
            )
            
            self.db.add(table_metadata)
            self.db.commit()
            self.db.refresh(table_metadata)
            return table_metadata
    
    async def save_table_metadata_config(
        self, 
        user_id: int, 
        database_config_id: int, 
        table_names: List[str]
    ) -> Dict[str, Any]:
        """保存表元数据配置（简化版，只保存基本信息）"""
        try:
            # 获取数据库配置
            db_config = self.db.query(DatabaseConfig).filter(
                and_(DatabaseConfig.id == database_config_id, DatabaseConfig.user_id == user_id)
            ).first()
            
            if not db_config:
                raise NotFoundError("数据库配置不存在")
            
            saved_tables = []
            failed_tables = []
            
            for table_name in table_names:
                try:
                    # 检查是否已存在
                    existing = self.db.query(TableMetadata).filter(
                        and_(
                            TableMetadata.user_id == user_id,
                            TableMetadata.database_config_id == database_config_id,
                            TableMetadata.table_name == table_name
                        )
                    ).first()
                    
                    if existing:
                        # 更新现有记录
                        existing.is_enabled_for_qa = True
                        existing.last_synced_at = datetime.utcnow()
                        saved_tables.append({
                            'table_name': table_name,
                            'action': 'updated'
                        })
                    else:
                        # 创建新记录
                        metadata = TableMetadata(
                            created_by=user_id,
                            database_config_id=database_config_id,
                            table_name=table_name,
                            table_schema='public',  # 默认值
                            table_type='table',     # 默认值
                            table_comment='',
                            columns_count=0,        # 后续可通过collect接口更新
                            row_count=0,           # 后续可通过collect接口更新
                            is_enabled_for_qa=True,
                            qa_description='',
                            business_context='',
                            sample_data='{}',
                            column_info='{}',
                            last_synced_at=datetime.utcnow()
                        )
                        
                        self.db.add(metadata)
                        saved_tables.append({
                            'table_name': table_name,
                            'action': 'created'
                        })
                        
                except Exception as e:
                    logger.error(f"保存表 {table_name} 配置失败: {str(e)}")
                    failed_tables.append({
                        'table_name': table_name,
                        'error': str(e)
                    })
            
            # 提交事务
            self.db.commit()
            
            return {
                'saved_tables': saved_tables,
                'failed_tables': failed_tables,
                'total_saved': len(saved_tables),
                'total_failed': len(failed_tables)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存表元数据配置失败: {str(e)}")
            raise e
    
    def get_user_table_metadata(
        self, 
        user_id: int, 
        database_config_id: Optional[int] = None
    ) -> List[TableMetadata]:
        """获取用户的表元数据列表"""
        query = self.db.query(TableMetadata).filter(TableMetadata.created_by == user_id)
        
        if database_config_id:
            query = query.filter(TableMetadata.database_config_id == database_config_id)
        
        return query.filter(TableMetadata.is_enabled_for_qa == True).all()
    
    def get_table_metadata_by_name(
        self,
        user_id: int,
        database_config_id: int,
        table_name: str
    ) -> Optional[TableMetadata]:
        """根据表名获取表元数据"""
        return self.db.query(TableMetadata).filter(
            and_(
                TableMetadata.created_by == user_id,
                TableMetadata.database_config_id == database_config_id,
                TableMetadata.table_name == table_name
            )
        ).first()
    
    def update_table_qa_settings(
        self, 
        user_id: int, 
        metadata_id: int, 
        settings: Dict[str, Any]
    ) -> bool:
        """更新表的问答设置"""
        try:
            metadata = self.db.query(TableMetadata).filter(
                and_(
                    TableMetadata.id == metadata_id,
                    TableMetadata.created_by == user_id
                )
            ).first()
            
            if not metadata:
                return False
            
            if 'is_enabled_for_qa' in settings:
                metadata.is_enabled_for_qa = settings['is_enabled_for_qa']
            if 'qa_description' in settings:
                metadata.qa_description = settings['qa_description']
            if 'business_context' in settings:
                metadata.business_context = settings['business_context']
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新表问答设置失败: {str(e)}")
            self.db.rollback()
            return False
    
    def save_table_metadata(
        self,
        user_id: int,
        database_config_id: int,
        table_name: str,
        columns_info: List[Dict[str, Any]],
        primary_keys: List[str],
        row_count: int,
        table_comment: str = ''
    ) -> TableMetadata:
        """保存单个表的元数据"""
        try:
            # 检查是否已存在
            existing = self.db.query(TableMetadata).filter(
                and_(
                    TableMetadata.created_by == user_id,
                    TableMetadata.database_config_id == database_config_id,
                    TableMetadata.table_name == table_name
                )
            ).first()
            
            if existing:
                # 更新现有记录
                existing.columns_info = columns_info
                existing.primary_keys = primary_keys
                existing.row_count = row_count
                existing.table_comment = table_comment
                existing.last_synced_at = datetime.utcnow()
                self.db.commit()
                return existing
            else:
                # 创建新记录
                metadata = TableMetadata(
                    created_by=user_id,
                    database_config_id=database_config_id,
                    table_name=table_name,
                    table_schema='public',
                    table_type='BASE TABLE',
                    table_comment=table_comment,
                    columns_info=columns_info,
                    primary_keys=primary_keys,
                    row_count=row_count,
                    is_enabled_for_qa=True,
                    last_synced_at=datetime.utcnow()
                )
                
                self.db.add(metadata)
                self.db.commit()
                self.db.refresh(metadata)
                return metadata
                
        except Exception as e:
            logger.error(f"保存表元数据失败: {str(e)}")
            self.db.rollback()
            raise e
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """解密密码（需要实现加密逻辑）"""
        # 这里需要实现与DatabaseConfigService相同的解密逻辑
        # 暂时返回原始密码
        return encrypted_password