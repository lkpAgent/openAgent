#!/usr/bin/env python3
"""测试知识库对话集成功能。"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 手动加载.env文件
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from sqlalchemy.orm import Session
from chat_agent.db.database import get_db
from chat_agent.services.knowledge_chat import KnowledgeChatService
from chat_agent.services.conversation import ConversationService
from chat_agent.services.knowledge_base import KnowledgeBaseService
from chat_agent.models.message import MessageRole
from chat_agent.utils.schemas import ConversationCreate
from chat_agent.core.config import settings

async def test_knowledge_chat_integration():
    """测试知识库对话集成功能。"""
    print("=== 测试知识库对话集成功能 ===")
    
    # 获取数据库会话
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # 初始化服务
        knowledge_chat_service = KnowledgeChatService(db)
        conversation_service = ConversationService(db)
        kb_service = KnowledgeBaseService(db)
        
        print(f"✓ 服务初始化成功")
        print(f"✓ LLM模型: {knowledge_chat_service.llm.model_name}")
        
        # 获取第一个知识库
        knowledge_bases = kb_service.get_knowledge_bases()
        if not knowledge_bases:
            print("❌ 没有找到知识库，请先创建知识库并上传文档")
            return
        
        kb = knowledge_bases[0]
        print(f"✓ 使用知识库: {kb.name} (ID: {kb.id})")
        
        # 创建测试对话
        conversation_data = ConversationCreate(
            title="知识库对话测试",
            model_name="doubao-lite-4k",
            temperature="0.7",
            max_tokens=2048
        )
        conversation = conversation_service.create_conversation(
            user_id=1,
            conversation_data=conversation_data
        )
        print(f"✓ 创建对话: {conversation.title} (ID: {conversation.id})")
        
        # 测试问题列表
        test_questions = [
            "什么是神经网络？",
            "请介绍一下深度学习的基本概念",
            "机器学习和人工智能有什么区别？",
            "能详细解释一下卷积神经网络吗？"
        ]
        
        print("\n=== 开始知识库对话测试 ===")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- 问题 {i}: {question} ---")
            
            try:
                # 使用知识库对话
                response = await knowledge_chat_service.chat_with_knowledge_base(
                    conversation_id=conversation.id,
                    message=question,
                    knowledge_base_id=kb.id,
                    stream=False
                )
                
                print(f"✓ 用户消息: {response.user_message.content[:50]}...")
                print(f"✓ AI回复: {response.assistant_message.content[:200]}...")
                print(f"✓ 使用模型: {response.model_used}")
                
                # 检查上下文文档
                if hasattr(response.assistant_message, 'context_documents') and response.assistant_message.context_documents:
                    print(f"✓ 检索到 {len(response.assistant_message.context_documents)} 个相关文档")
                    for j, doc in enumerate(response.assistant_message.context_documents[:2]):
                        print(f"  - 文档 {j+1}: {doc.get('source', 'unknown')} (内容: {doc.get('content', '')[:100]}...)")
                else:
                    print("⚠️ 未找到上下文文档")
                
            except Exception as e:
                print(f"❌ 对话失败: {str(e)}")
                continue
        
        # 测试对话历史
        print("\n=== 测试对话历史 ===")
        messages = conversation_service.get_conversation_messages(conversation.id)
        print(f"✓ 对话历史包含 {len(messages)} 条消息")
        
        for msg in messages[-4:]:  # 显示最后4条消息
            role_name = "用户" if msg.role == MessageRole.USER else "AI"
            print(f"  {role_name}: {msg.content[:100]}...")
        
        # 测试流式对话
        print("\n=== 测试流式对话 ===")
        stream_question = "请总结一下我们刚才讨论的内容"
        print(f"问题: {stream_question}")
        
        try:
            print("AI回复: ", end="", flush=True)
            full_response = ""
            async for chunk in knowledge_chat_service.chat_stream_with_knowledge_base(
                conversation_id=conversation.id,
                message=stream_question,
                knowledge_base_id=kb.id
            ):
                print(chunk, end="", flush=True)
                full_response += chunk
            
            print(f"\n✓ 流式对话完成，总长度: {len(full_response)} 字符")
            
        except Exception as e:
            print(f"\n❌ 流式对话失败: {str(e)}")
        
        print("\n=== 知识库对话集成测试完成 ===")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_knowledge_chat_integration())