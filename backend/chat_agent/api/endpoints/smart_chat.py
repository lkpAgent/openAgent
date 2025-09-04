from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from chat_agent.db.database import get_db
from chat_agent.services.auth import AuthService
from chat_agent.services.smart_workflow import SmartWorkflowManager
from chat_agent.services.conversation import ConversationService
from chat_agent.services.conversation_context import conversation_context_service
from chat_agent.utils.schemas import BaseResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/smart-chat", tags=["smart-chat"])
security = HTTPBearer()

# Request/Response Models
class SmartQueryRequest(BaseModel):
    query: str
    conversation_id: Optional[int] = None
    is_new_conversation: bool = False

class SmartQueryResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    workflow_steps: Optional[list] = None
    conversation_id: Optional[int] = None

class ConversationContextResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

@router.post("/query", response_model=SmartQueryResponse)
async def smart_query(
    request: SmartQueryRequest,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    智能问数查询接口
    支持新对话时自动加载文件列表，智能选择相关Excel文件，生成和执行pandas代码
    """
    conversation_id = None
    
    try:
        # 验证请求参数
        if not request.query or not request.query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="查询内容不能为空"
            )
        
        if len(request.query) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="查询内容过长，请控制在1000字符以内"
            )
        
        # 初始化工作流管理器
        workflow_manager = SmartWorkflowManager(db)
        conversation_service = ConversationService(db)
        
        # 处理对话上下文
        conversation_id = request.conversation_id
        
        # 如果是新对话或没有指定对话ID，创建新对话
        if request.is_new_conversation or not conversation_id:
            try:
                conversation_id = await conversation_context_service.create_conversation(
                    user_id=current_user.id,
                    title=f"智能问数: {request.query[:20]}..."
                )
                request.is_new_conversation = True
                logger.info(f"创建新对话: {conversation_id}")
            except Exception as e:
                logger.warning(f"创建对话失败，使用临时会话: {e}")
                conversation_id = None
        else:
            # 验证对话是否存在且属于当前用户
            try:
                context = await conversation_context_service.get_conversation_context(conversation_id)
                if not context or context.get('user_id') != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="对话不存在或无权访问"
                    )
                logger.info(f"使用现有对话: {conversation_id}")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"验证对话失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="对话验证失败"
                )
        
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
                # 不阻断流程，继续执行查询
        
        # 执行智能查询工作流
        try:
            result = await workflow_manager.process_smart_query(
                user_query=request.query,
                user_id=current_user.id,
                conversation_id=conversation_id,
                is_new_conversation=request.is_new_conversation
            )
        except Exception as e:
            logger.error(f"智能查询执行失败: {e}")
            # 返回结构化的错误响应
            return SmartQueryResponse(
                success=False,
                message=f"查询执行失败: {str(e)}",
                data={'error_type': 'query_execution_error'},
                workflow_steps=[{
                    'step': 'error',
                    'status': 'failed',
                    'message': str(e)
                }],
                conversation_id=conversation_id
            )
        
        # 如果查询成功，保存助手回复和更新上下文
        if result['success'] and conversation_id:
            try:
                # 保存助手回复
                await conversation_context_service.save_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=result.get('data', {}).get('summary', '查询完成'),
                    metadata={
                        'query_result': result.get('data'),
                        'workflow_steps': result.get('workflow_steps', []),
                        'selected_files': result.get('data', {}).get('used_files', [])
                    }
                )
                
                # 更新对话上下文
                await conversation_context_service.update_conversation_context(
                    conversation_id=conversation_id,
                    query=request.query,
                    selected_files=result.get('data', {}).get('used_files', [])
                )
                
                logger.info(f"查询成功完成，对话ID: {conversation_id}")
                
            except Exception as e:
                logger.warning(f"保存消息到对话历史失败: {e}")
                # 不影响返回结果，只记录警告
        
        # 返回结果，包含对话ID
        response_data = result.get('data', {})
        if conversation_id:
            response_data['conversation_id'] = conversation_id
        
        return SmartQueryResponse(
            success=result['success'],
            message=result.get('message', '查询完成'),
            data=response_data,
            workflow_steps=result.get('workflow_steps', []),
            conversation_id=conversation_id
        )
        
    except HTTPException:
        print(e)
        raise
    except Exception as e:
        logger.error(f"智能查询接口异常: {e}", exc_info=True)
        # 返回通用错误响应
        return SmartQueryResponse(
            success=False,
            message="服务器内部错误，请稍后重试",
            data={'error_type': 'internal_server_error'},
            workflow_steps=[{
                'step': 'error',
                'status': 'failed',
                'message': '系统异常'
            }],
            conversation_id=conversation_id
        )

@router.get("/conversation/{conversation_id}/context", response_model=ConversationContextResponse)
async def get_conversation_context(
    conversation_id: int,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取对话上下文信息，包括已使用的文件和历史查询
    """
    try:
        # 获取对话上下文
        context = await conversation_context_service.get_conversation_context(conversation_id)
        
        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话上下文不存在"
            )
        
        # 验证用户权限
        if context['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此对话"
            )
        
        # 获取对话历史
        history = await conversation_context_service.get_conversation_history(conversation_id)
        context['message_history'] = history
        
        return ConversationContextResponse(
            success=True,
            message="获取对话上下文成功",
            data=context
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话上下文失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话上下文失败: {str(e)}"
        )

@router.get("/files/status", response_model=ConversationContextResponse)
async def get_files_status(
    current_user = Depends(AuthService.get_current_user)
):
    """
    获取用户当前的文件状态和统计信息
    """
    try:
        workflow_manager = SmartWorkflowManager()
        
        # 获取用户文件列表
        file_list = await workflow_manager._load_user_file_list(current_user.id)
        
        # 统计信息
        total_files = len(file_list)
        total_rows = sum(f.get('row_count', 0) for f in file_list)
        total_columns = sum(f.get('column_count', 0) for f in file_list)
        
        # 文件类型统计
        file_types = {}
        for file_info in file_list:
            filename = file_info['filename']
            ext = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
            file_types[ext] = file_types.get(ext, 0) + 1
        
        status_data = {
            'total_files': total_files,
            'total_rows': total_rows,
            'total_columns': total_columns,
            'file_types': file_types,
            'files': [{
                'id': f['id'],
                'filename': f['filename'],
                'row_count': f.get('row_count', 0),
                'column_count': f.get('column_count', 0),
                'columns': f.get('columns', []),
                'upload_time': f.get('upload_time')
            } for f in file_list],
            'ready_for_query': total_files > 0
        }
        
        return ConversationContextResponse(
            success=True,
            message=f"当前有{total_files}个可用文件" if total_files > 0 else "暂无可用文件，请先上传Excel文件",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"获取文件状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件状态失败: {str(e)}"
        )

@router.post("/conversation/{conversation_id}/reset")
async def reset_conversation_context(
    conversation_id: int,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    重置对话上下文，清除历史查询记录但保留文件
    """
    try:
        # 验证对话存在和用户权限
        context = await conversation_context_service.get_conversation_context(conversation_id)
        
        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话上下文不存在"
            )
        
        if context['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此对话"
            )
        
        # 重置对话上下文
        success = await conversation_context_service.reset_conversation_context(conversation_id)
        
        if success:
            return {
                "success": True,
                "message": "对话上下文已重置，可以开始新的数据分析会话"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="重置对话上下文失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置对话上下文失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置对话上下文失败: {str(e)}"
        )