from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from sqlalchemy.orm import Session
from open_agent.models.conversation import Conversation
from open_agent.models.message import Message
from open_agent.db.database import get_db

class ConversationContextService:
    """
    对话上下文管理服务
    用于管理智能问数的对话历史和上下文信息
    """
    
    def __init__(self):
        self.context_cache = {}  # 内存缓存对话上下文
    
    async def create_conversation(self, user_id: int, title: str = "智能问数对话") -> int:
        """
        创建新的对话
        
        Args:
            user_id: 用户ID
            title: 对话标题
            
        Returns:
            新创建的对话ID
        """
        try:
            db = next(get_db())
            
            conversation = Conversation(
                user_id=user_id,
                title=title,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            # 初始化对话上下文
            self.context_cache[conversation.id] = {
                'conversation_id': conversation.id,
                'user_id': user_id,
                'file_list': [],
                'selected_files': [],
                'query_history': [],
                'created_at': datetime.utcnow().isoformat()
            }
            
            return conversation.id
            
        except Exception as e:
            print(f"创建对话失败: {e}")
            raise
        finally:
            db.close()
    
    async def get_conversation_context(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """
        获取对话上下文
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话上下文信息
        """
        # 先从缓存中查找
        if conversation_id in self.context_cache:
            return self.context_cache[conversation_id]
        
        # 从数据库加载
        try:
            db = next(get_db())
            
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                return None
            
            # 加载消息历史
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at).all()
            
            # 重建上下文
            context = {
                'conversation_id': conversation_id,
                'user_id': conversation.user_id,
                'file_list': [],
                'selected_files': [],
                'query_history': [],
                'created_at': conversation.created_at.isoformat()
            }
            
            # 从消息中提取查询历史
            for message in messages:
                if message.role == 'user':
                    context['query_history'].append({
                        'query': message.content,
                        'timestamp': message.created_at.isoformat()
                    })
                elif message.role == 'assistant' and message.metadata:
                    # 从助手消息的元数据中提取文件信息
                    try:
                        metadata = json.loads(message.metadata) if isinstance(message.metadata, str) else message.metadata
                        if 'selected_files' in metadata:
                            context['selected_files'] = metadata['selected_files']
                        if 'file_list' in metadata:
                            context['file_list'] = metadata['file_list']
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            # 缓存上下文
            self.context_cache[conversation_id] = context
            
            return context
            
        except Exception as e:
            print(f"获取对话上下文失败: {e}")
            return None
        finally:
            db.close()
    
    async def update_conversation_context(
        self, 
        conversation_id: int, 
        file_list: List[Dict[str, Any]] = None,
        selected_files: List[Dict[str, Any]] = None,
        query: str = None
    ) -> bool:
        """
        更新对话上下文
        
        Args:
            conversation_id: 对话ID
            file_list: 文件列表
            selected_files: 选中的文件
            query: 用户查询
            
        Returns:
            更新是否成功
        """
        try:
            # 获取或创建上下文
            context = await self.get_conversation_context(conversation_id)
            if not context:
                return False
            
            # 更新上下文信息
            if file_list is not None:
                context['file_list'] = file_list
            
            if selected_files is not None:
                context['selected_files'] = selected_files
            
            if query is not None:
                context['query_history'].append({
                    'query': query,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # 更新缓存
            self.context_cache[conversation_id] = context
            
            return True
            
        except Exception as e:
            print(f"更新对话上下文失败: {e}")
            return False
    
    async def save_message(
        self, 
        conversation_id: int, 
        role: str, 
        content: str, 
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        保存消息到数据库
        
        Args:
            conversation_id: 对话ID
            role: 消息角色 (user/assistant)
            content: 消息内容
            metadata: 元数据
            
        Returns:
            保存是否成功
        """
        try:
            db = next(get_db())
            
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                metadata=json.dumps(metadata) if metadata else None,
                created_at=datetime.utcnow()
            )
            
            db.add(message)
            db.commit()
            
            # 更新对话的最后更新时间
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if conversation:
                conversation.updated_at = datetime.utcnow()
                db.commit()
            
            return True
            
        except Exception as e:
            print(f"保存消息失败: {e}")
            return False
        finally:
            db.close()
    
    async def reset_conversation_context(self, conversation_id: int) -> bool:
        """
        重置对话上下文
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            重置是否成功
        """
        try:
            # 清除缓存
            if conversation_id in self.context_cache:
                context = self.context_cache[conversation_id]
                # 保留基本信息，清除文件和查询历史
                context.update({
                    'file_list': [],
                    'selected_files': [],
                    'query_history': []
                })
            
            return True
            
        except Exception as e:
            print(f"重置对话上下文失败: {e}")
            return False
    
    async def get_conversation_history(self, conversation_id: int) -> List[Dict[str, Any]]:
        """
        获取对话历史消息
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            消息历史列表
        """
        try:
            db = next(get_db())
            
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at).all()
            
            history = []
            for message in messages:
                msg_data = {
                    'id': message.id,
                    'role': message.role,
                    'content': message.content,
                    'timestamp': message.created_at.isoformat()
                }
                
                if message.metadata:
                    try:
                        metadata = json.loads(message.metadata) if isinstance(message.metadata, str) else message.metadata
                        msg_data['metadata'] = metadata
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                history.append(msg_data)
            
            return history
            
        except Exception as e:
            print(f"获取对话历史失败: {e}")
            return []
        finally:
            db.close()
    
    def clear_cache(self, conversation_id: int = None):
        """
        清除缓存
        
        Args:
            conversation_id: 特定对话ID，如果为None则清除所有缓存
        """
        if conversation_id:
            self.context_cache.pop(conversation_id, None)
        else:
            self.context_cache.clear()

# 全局实例
conversation_context_service = ConversationContextService()