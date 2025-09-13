from typing import Dict, Any, List, Optional, Union
import logging
from .smart_excel_workflow import SmartExcelWorkflowManager
from .smart_db_workflow import SmartDatabaseWorkflowManager

logger = logging.getLogger(__name__)

# 异常类已迁移到各自的工作流文件中

class SmartWorkflowManager:
    """
    智能工作流管理器
    统一入口，委托给具体的Excel或数据库工作流管理器
    """
    
    def __init__(self, db=None):
        self.db = db
        self.excel_workflow = SmartExcelWorkflowManager(db)
        self.database_workflow = SmartDatabaseWorkflowManager(db)
    
    async def process_excel_query_stream(
        self, 
        user_query: str, 
        user_id: int, 
        conversation_id: Optional[int] = None,
        is_new_conversation: bool = False
    ):
        """
        流式处理Excel智能问数查询，委托给Excel工作流管理器
        """
        async for result in self.excel_workflow.process_excel_query_stream(
            user_query, user_id, conversation_id, is_new_conversation
        ):
            yield result
    
    async def process_database_query_stream(
        self, 
        user_query: str,
        user_id: int,
        database_config_id: int,
        conversation_id: Optional[int] = None,
        is_new_conversation: bool = False
    ):
        """
        流式处理数据库智能问数查询，委托给数据库工作流管理器
        """
        async for result in self.database_workflow.process_database_query_stream(
            user_query, user_id, database_config_id
        ):
            yield result
    
    async def process_smart_query(
        self, 
        user_query: str, 
        user_id: int, 
        conversation_id: Optional[int] = None,
        is_new_conversation: bool = False
    ) -> Dict[str, Any]:
        """
        处理智能问数查询的主要工作流（非流式版本）
        委托给Excel工作流管理器
        """
        return await self.excel_workflow.process_smart_query(
            user_query=user_query,
            user_id=user_id,
            conversation_id=conversation_id,
            is_new_conversation=is_new_conversation
        )
    
    async def process_database_query(
        self, 
        user_query: str, 
        user_id: int, 
        database_config_id: int,
        conversation_id: Optional[int] = None,
        is_new_conversation: bool = False
    ) -> Dict[str, Any]:
        """
        处理数据库智能问数查询，委托给数据库工作流管理器
        """
        return await self.database_workflow.process_database_query(
            user_query, user_id, database_config_id, None, conversation_id, is_new_conversation
        )