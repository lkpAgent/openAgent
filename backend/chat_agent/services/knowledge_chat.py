"""Knowledge base chat service using LangChain RAG."""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import Chroma
from .embedding_factory import EmbeddingFactory

from ..core.config import settings
from ..models.message import MessageRole
from ..utils.schemas import ChatResponse, MessageResponse
from ..utils.exceptions import ChatServiceError
from ..utils.logger import get_logger
from .conversation import ConversationService
from .document_processor import document_processor

logger = get_logger("knowledge_chat_service")


class KnowledgeChatService:
    """Knowledge base chat service using LangChain RAG."""
    
    def __init__(self, db: Session):
        self.db = db
        self.conversation_service = ConversationService(db)
        
        # 获取当前LLM配置
        llm_config = settings.llm.get_current_config()
        
        # Initialize LangChain ChatOpenAI
        self.llm = ChatOpenAI(
            model=llm_config["model"],
            api_key=llm_config["api_key"],
            base_url=llm_config["base_url"],
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"],
            streaming=False
        )
        
        # Streaming LLM for stream responses
        self.streaming_llm = ChatOpenAI(
            model=llm_config["model"],
            api_key=llm_config["api_key"],
            base_url=llm_config["base_url"],
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"],
            streaming=True
        )
        
        # Initialize embeddings based on provider
        self.embeddings = EmbeddingFactory.create_embeddings()
        
        logger.info(f"Knowledge Chat Service initialized with model: {self.llm.model_name}")
    
    def _get_vector_store(self, knowledge_base_id: int) -> Optional[Chroma]:
        """Get vector store for knowledge base."""
        try:
            import os
            kb_vector_path = os.path.join(document_processor.vector_db_path, f"kb_{knowledge_base_id}")
            
            if not os.path.exists(kb_vector_path):
                logger.warning(f"Vector store not found for knowledge base {knowledge_base_id}")
                return None
            
            vector_store = Chroma(
                persist_directory=kb_vector_path,
                embedding_function=self.embeddings
            )
            
            return vector_store
            
        except Exception as e:
            logger.error(f"Failed to load vector store for KB {knowledge_base_id}: {str(e)}")
            return None
    
    def _create_rag_chain(self, vector_store: Chroma, conversation_history: List[Dict[str, str]]):
        """Create RAG chain with conversation history."""
        
        # Create retriever
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Create prompt template
        system_prompt = """你是一个智能助手，基于提供的上下文信息回答用户问题。

上下文信息：
{context}

请根据上下文信息回答用户的问题。如果上下文信息不足以回答问题，请诚实地说明。
保持回答准确、有用且简洁。"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        # Create chain
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        rag_chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough(),
                "chat_history": lambda x: conversation_history
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain, retriever
    
    def _prepare_conversation_history(self, messages: List) -> List[Dict[str, str]]:
        """Prepare conversation history for RAG chain."""
        history = []
        
        for msg in messages[:-1]:  # Exclude the last message (current user message)
            if msg.role == MessageRole.USER:
                history.append({"role": "human", "content": msg.content})
            elif msg.role == MessageRole.ASSISTANT:
                history.append({"role": "assistant", "content": msg.content})
        
        return history
    
    async def chat_with_knowledge_base(
        self,
        conversation_id: int,
        message: str,
        knowledge_base_id: int,
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ChatResponse:
        """Chat with knowledge base using RAG."""
        
        try:
            # Get conversation and validate
            conversation = self.conversation_service.get_conversation(conversation_id)
            if not conversation:
                raise ChatServiceError("Conversation not found")
            
            # Get vector store
            vector_store = self._get_vector_store(knowledge_base_id)
            if not vector_store:
                raise ChatServiceError(f"Knowledge base {knowledge_base_id} not found or not processed")
            
            # Save user message
            user_message = self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=message,
                role=MessageRole.USER
            )
            
            # Get conversation history
            messages = self.conversation_service.get_conversation_messages(conversation_id)
            conversation_history = self._prepare_conversation_history(messages)
            
            # Create RAG chain
            rag_chain, retriever = self._create_rag_chain(vector_store, conversation_history)
            
            # Get relevant documents for context
            relevant_docs = retriever.get_relevant_documents(message)
            context_documents = []
            
            for doc in relevant_docs:
                context_documents.append({
                    "content": doc.page_content[:500],  # Limit content length
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("filename", "unknown")
                })
            
            # Generate response
            if stream:
                # For streaming, we'll use a different approach
                response_content = await self._generate_streaming_response(
                    rag_chain, message, conversation_id
                )
            else:
                response_content = await asyncio.to_thread(rag_chain.invoke, message)
            
            # Save assistant message with context
            assistant_message = self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=response_content,
                role=MessageRole.ASSISTANT,
                context_documents=context_documents
            )
            
            # Create response
            return ChatResponse(
                user_message=MessageResponse.from_orm(user_message),
                assistant_message=MessageResponse.from_orm(assistant_message),
                model_used=self.llm.model_name,
                total_tokens=None  # TODO: Calculate tokens if needed
            )
            
        except Exception as e:
            logger.error(f"Knowledge base chat failed: {str(e)}")
            raise ChatServiceError(f"Knowledge base chat failed: {str(e)}")
    
    async def _generate_streaming_response(
        self,
        rag_chain,
        message: str,
        conversation_id: int
    ) -> str:
        """Generate streaming response (placeholder for now)."""
        # For now, use non-streaming approach
        # TODO: Implement proper streaming with RAG chain
        return await asyncio.to_thread(rag_chain.invoke, message)
    
    async def chat_stream_with_knowledge_base(
        self,
        conversation_id: int,
        message: str,
        knowledge_base_id: int,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Chat with knowledge base using RAG with streaming response."""
        
        try:
            # Get conversation and validate
            conversation = self.conversation_service.get_conversation(conversation_id)
            if not conversation:
                raise ChatServiceError("Conversation not found")
            
            # Get vector store
            vector_store = self._get_vector_store(knowledge_base_id)
            if not vector_store:
                raise ChatServiceError(f"Knowledge base {knowledge_base_id} not found or not processed")
            
            # Get conversation history
            messages = self.conversation_service.get_conversation_messages(conversation_id)
            conversation_history = self._prepare_conversation_history(messages)
            
            # Create RAG chain
            rag_chain, retriever = self._create_rag_chain(vector_store, conversation_history)
            
            # Save user message
            user_message = self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=message,
                role=MessageRole.USER
            )
            
            # Get relevant documents
            relevant_docs = retriever.get_relevant_documents(message)
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Create streaming LLM
            llm_config = settings.llm.get_current_config()
            streaming_llm = ChatOpenAI(
                model=llm_config["model"],
                temperature=temperature or llm_config["temperature"],
                max_tokens=max_tokens or llm_config["max_tokens"],
                streaming=True,
                api_key=llm_config["api_key"],
                base_url=llm_config["base_url"]
            )
            
            # Create prompt for streaming
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个智能助手。请基于以下上下文信息回答用户的问题。如果上下文中没有相关信息，请诚实地说明。\n\n上下文信息：\n{context}"),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}")
            ])
            
            # Prepare chat history for prompt
            chat_history_messages = []
            for hist in conversation_history:
                if hist["role"] == "human":
                    chat_history_messages.append(HumanMessage(content=hist["content"]))
                elif hist["role"] == "assistant":
                    chat_history_messages.append(AIMessage(content=hist["content"]))
            
            # Create streaming chain
            streaming_chain = (
                {
                    "context": lambda x: context,
                    "chat_history": lambda x: chat_history_messages,
                    "question": lambda x: x["question"]
                }
                | prompt
                | streaming_llm
                | StrOutputParser()
            )
            
            # Generate streaming response
            full_response = ""
            async for chunk in streaming_chain.astream({"question": message}):
                if chunk:
                    full_response += chunk
                    yield chunk
            
            # Save assistant response
            if full_response:
                self.conversation_service.add_message(
                    conversation_id=conversation_id,
                    content=full_response,
                    role=MessageRole.ASSISTANT,
                    message_metadata={
                        "knowledge_base_id": knowledge_base_id,
                        "relevant_docs_count": len(relevant_docs)
                    }
                )
            
        except Exception as e:
            logger.error(f"Error in knowledge base streaming chat: {str(e)}")
            error_message = f"知识库对话出错: {str(e)}"
            yield error_message
            
            # Save error message
            self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=error_message,
                role=MessageRole.ASSISTANT
            )
    
    async def search_knowledge_base(
        self,
        knowledge_base_id: int,
        query: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant documents."""
        
        try:
            vector_store = self._get_vector_store(knowledge_base_id)
            if not vector_store:
                return []
            
            # Perform similarity search
            results = vector_store.similarity_search_with_score(query, k=k)
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score),
                    "source": doc.metadata.get("filename", "unknown")
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Knowledge base search failed: {str(e)}")
            return []