"""WebSocket连接管理器，用于实时推送工作流执行状态"""

import json
import asyncio
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from ..utils.logger import get_logger

logger = get_logger("websocket_manager")


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃的WebSocket连接
        self.active_connections: Dict[str, WebSocket] = {}
        # 存储用户ID到连接ID的映射
        self.user_connections: Dict[int, Set[str]] = {}
        # 存储工作流执行ID到连接ID的映射
        self.execution_connections: Dict[int, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: int):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        # 添加用户连接映射
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        logger.info(f"WebSocket连接已建立: {connection_id}, 用户: {user_id}")
    
    def disconnect(self, connection_id: str, user_id: int):
        """断开WebSocket连接"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # 移除用户连接映射
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # 移除执行连接映射
        for execution_id in list(self.execution_connections.keys()):
            self.execution_connections[execution_id].discard(connection_id)
            if not self.execution_connections[execution_id]:
                del self.execution_connections[execution_id]
        
        logger.info(f"WebSocket连接已断开: {connection_id}, 用户: {user_id}")
    
    def subscribe_to_execution(self, connection_id: str, execution_id: int):
        """订阅工作流执行状态更新"""
        if execution_id not in self.execution_connections:
            self.execution_connections[execution_id] = set()
        self.execution_connections[execution_id].add(connection_id)
        logger.info(f"连接 {connection_id} 订阅了执行 {execution_id}")
    
    def unsubscribe_from_execution(self, connection_id: str, execution_id: int):
        """取消订阅工作流执行状态更新"""
        if execution_id in self.execution_connections:
            self.execution_connections[execution_id].discard(connection_id)
            if not self.execution_connections[execution_id]:
                del self.execution_connections[execution_id]
        logger.info(f"连接 {connection_id} 取消订阅执行 {execution_id}")
    
    async def send_personal_message(self, message: str, connection_id: str):
        """发送个人消息"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(message)
            except Exception as e:
                logger.error(f"发送消息失败: {connection_id}, 错误: {e}")
                # 连接可能已断开，移除它
                if connection_id in self.active_connections:
                    del self.active_connections[connection_id]
    
    async def send_to_user(self, message: str, user_id: int):
        """发送消息给特定用户的所有连接"""
        if user_id in self.user_connections:
            disconnected_connections = []
            for connection_id in self.user_connections[user_id]:
                try:
                    await self.send_personal_message(message, connection_id)
                except Exception as e:
                    logger.error(f"发送用户消息失败: {user_id}, 连接: {connection_id}, 错误: {e}")
                    disconnected_connections.append(connection_id)
            
            # 清理断开的连接
            for connection_id in disconnected_connections:
                self.disconnect(connection_id, user_id)
    
    async def broadcast_to_execution(self, message: str, execution_id: int):
        """广播消息给订阅特定执行的所有连接"""
        if execution_id in self.execution_connections:
            disconnected_connections = []
            for connection_id in self.execution_connections[execution_id]:
                try:
                    await self.send_personal_message(message, connection_id)
                except Exception as e:
                    logger.error(f"广播执行消息失败: {execution_id}, 连接: {connection_id}, 错误: {e}")
                    disconnected_connections.append(connection_id)
            
            # 清理断开的连接
            for connection_id in disconnected_connections:
                if connection_id in self.active_connections:
                    # 找到用户ID来正确断开连接
                    for user_id, connections in self.user_connections.items():
                        if connection_id in connections:
                            self.disconnect(connection_id, user_id)
                            break
    
    async def send_execution_update(self, execution_id: int, update_type: str, data: Dict[str, Any]):
        """发送工作流执行更新"""
        message = {
            "type": "execution_update",
            "execution_id": execution_id,
            "update_type": update_type,  # "workflow_started", "node_started", "node_completed", "workflow_completed", "workflow_failed"
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.broadcast_to_execution(json.dumps(message), execution_id)
        logger.info(f"发送执行更新: {execution_id}, 类型: {update_type}")
    
    async def send_node_update(self, execution_id: int, node_id: str, node_execution_data: Dict[str, Any]):
        """发送节点执行更新"""
        await self.send_execution_update(
            execution_id=execution_id,
            update_type="node_update",
            data={
                "node_id": node_id,
                "node_execution": node_execution_data
            }
        )
    
    async def send_workflow_status(self, execution_id: int, status: str, data: Optional[Dict[str, Any]] = None):
        """发送工作流状态更新"""
        await self.send_execution_update(
            execution_id=execution_id,
            update_type="workflow_status",
            data={
                "status": status,
                "data": data or {}
            }
        )
    
    async def send_node_status(self, execution_id: int, node_id: str, status: str, data: Optional[Dict[str, Any]] = None):
        """发送节点状态更新"""
        await self.send_execution_update(
            execution_id=execution_id,
            update_type="node_status",
            data={
                "node_id": node_id,
                "status": status,
                "data": data or {}
            }
        )


# 全局连接管理器实例
_connection_manager = None

def get_connection_manager() -> ConnectionManager:
    """获取全局连接管理器实例"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager