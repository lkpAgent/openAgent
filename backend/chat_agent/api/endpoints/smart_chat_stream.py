from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, AsyncGenerator
import json
import asyncio
from datetime import datetime

from chat_agent.db.database import get_db
from chat_agent.services.auth import AuthService
from chat_agent.services.smart_workflow import SmartWorkflowManager
from chat_agent.services.conversation_context import ConversationContextService
import logging
from pydantic import BaseModel
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/smart-chat-stream", tags=["智能问答流式接口"])

class StreamQueryRequest(BaseModel):
    query: str
    conversation_id: Optional[int] = None
    is_new_conversation: bool = False

@router.post("/query")
async def stream_smart_query(
    request: StreamQueryRequest,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    流式智能问答查询接口
    支持实时推送工作流步骤和最终结果
    """
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        conversation_id = None
        workflow_manager = None
        
        try:
            # 验证请求参数
            if not request.query or not request.query.strip():
                yield f"data: {json.dumps({'type': 'error', 'message': '查询内容不能为空'}, ensure_ascii=False)}\n\n"
                return
            
            if len(request.query) > 1000:
                yield f"data: {json.dumps({'type': 'error', 'message': '查询内容过长，请控制在1000字符以内'}, ensure_ascii=False)}\n\n"
                return
            
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'message': '开始处理查询', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 初始化服务
            workflow_manager = SmartWorkflowManager(db)
            conversation_context_service = ConversationContextService()
            
            # 处理对话上下文
            conversation_id = request.conversation_id
            
            # 如果是新对话或没有指定对话ID，创建新对话
            if request.is_new_conversation or not conversation_id:
                try:
                    conversation_id = await conversation_context_service.create_conversation(
                        user_id=current_user.id,
                        title=f"智能问数: {request.query[:20]}..."
                    )
                    yield f"data: {json.dumps({'type': 'conversation_created', 'conversation_id': conversation_id}, ensure_ascii=False)}\n\n"
                except Exception as e:
                    logger.warning(f"创建对话失败: {e}")
                    # 不阻断流程，继续执行查询
            
            # 保存用户消息
            if conversation_id:
                try:
                    await conversation_context_service.save_message(
                        conversation_id=conversation_id,
                        role="user",
                        content=request.query
                    )
                except Exception as e:
                    logger.warning(f"保存用户消息失败: {e}")
            
            # 执行智能查询工作流（带流式推送）
            async for step_data in workflow_manager.process_smart_query_stream(
                user_query=request.query,
                user_id=current_user.id,
                conversation_id=conversation_id,
                is_new_conversation=request.is_new_conversation
            ):
                # 推送工作流步骤
                yield f"data: {json.dumps(step_data, ensure_ascii=False)}\n\n"
                
                # 如果是最终结果，保存到对话历史
                if step_data.get('type') == 'final_result' and conversation_id:
                    try:
                        result_data = step_data.get('data', {})
                        await conversation_context_service.save_message(
                            conversation_id=conversation_id,
                            role="assistant",
                            content=result_data.get('summary', '查询完成'),
                            metadata={
                                'query_result': result_data,
                                'workflow_steps': step_data.get('workflow_steps', []),
                                'selected_files': result_data.get('used_files', [])
                            }
                        )
                        
                        # 更新对话上下文
                        await conversation_context_service.update_conversation_context(
                            conversation_id=conversation_id,
                            query=request.query,
                            selected_files=result_data.get('used_files', [])
                        )
                        
                        logger.info(f"查询成功完成，对话ID: {conversation_id}")
                        
                    except Exception as e:
                        logger.warning(f"保存消息到对话历史失败: {e}")
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'complete', 'message': '查询处理完成', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"流式智能查询异常: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': f'查询执行失败: {str(e)}'}, ensure_ascii=False)}\n\n"
        
        finally:
            # 清理资源
            if workflow_manager:
                try:
                    workflow_manager.executor.shutdown(wait=False)
                except:
                    pass
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        }
    )