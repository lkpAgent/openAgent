"""WebSocket API端点"""

import json
import uuid
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...models.user import User
from ...services.auth import AuthService
from ...services.websocket_manager import get_connection_manager
from ...utils.logger import get_logger

logger = get_logger("websocket_api")

router = APIRouter()


async def get_current_user_from_token(token: str, db: Session) -> Optional[User]:
    """从token获取当前用户（WebSocket专用）"""
    try:
        auth_service = AuthService()
        payload = auth_service.verify_token(token)
        if payload is None:
            return None
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    except Exception as e:
        logger.error(f"WebSocket认证失败: {e}")
        return None


@router.websocket("/ws/workflow-execution")
async def websocket_workflow_execution(
    websocket: WebSocket,
    token: str = Query(..., description="认证token"),
    db: Session = Depends(get_db)
):
    """工作流执行WebSocket连接"""
    connection_manager = get_connection_manager()
    connection_id = str(uuid.uuid4())
    
    # 验证用户身份
    user = await get_current_user_from_token(token, db)
    if not user:
        await websocket.close(code=4001, reason="认证失败")
        return
    
    try:
        # 建立连接
        await connection_manager.connect(websocket, connection_id, user.id)
        
        # 发送连接确认消息
        await connection_manager.send_personal_message(
            json.dumps({
                "type": "connection_established",
                "connection_id": connection_id,
                "user_id": user.id,
                "message": "WebSocket连接已建立"
            }),
            connection_id
        )
        
        # 监听客户端消息
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理不同类型的消息
                message_type = message.get("type")
                
                if message_type == "subscribe_execution":
                    # 订阅工作流执行状态
                    execution_id = message.get("execution_id")
                    if execution_id:
                        connection_manager.subscribe_to_execution(connection_id, execution_id)
                        await connection_manager.send_personal_message(
                            json.dumps({
                                "type": "subscription_confirmed",
                                "execution_id": execution_id,
                                "message": f"已订阅执行 {execution_id}"
                            }),
                            connection_id
                        )
                
                elif message_type == "unsubscribe_execution":
                    # 取消订阅工作流执行状态
                    execution_id = message.get("execution_id")
                    if execution_id:
                        connection_manager.unsubscribe_from_execution(connection_id, execution_id)
                        await connection_manager.send_personal_message(
                            json.dumps({
                                "type": "unsubscription_confirmed",
                                "execution_id": execution_id,
                                "message": f"已取消订阅执行 {execution_id}"
                            }),
                            connection_id
                        )
                
                elif message_type == "ping":
                    # 心跳检测
                    await connection_manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "timestamp": message.get("timestamp")
                        }),
                        connection_id
                    )
                
                else:
                    logger.warning(f"未知消息类型: {message_type}")
                    
            except json.JSONDecodeError:
                logger.error(f"无效的JSON消息: {data}")
                await connection_manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "无效的JSON格式"
                    }),
                    connection_id
                )
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    finally:
        # 清理连接
        connection_manager.disconnect(connection_id, user.id)


@router.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    """测试WebSocket连接"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info("测试WebSocket连接断开")