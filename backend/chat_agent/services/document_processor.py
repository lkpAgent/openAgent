"""文档处理服务，负责文档的分段、向量化和索引"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib.parse import quote
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader
)
import pdfplumber
from langchain.schema import Document
from langchain_postgres import PGVector
from typing import List
# 旧的ZhipuEmbeddings类已移除，现在统一使用EmbeddingFactory创建embedding实例

from ..core.config import settings
from ..utils.file_utils import FileUtils
from ..models.knowledge_base import Document as DocumentModel
from ..db.database import get_db

logger = logging.getLogger(__name__)


class PGVectorConnectionPool:
    """PGVector连接池管理器"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._init_connection_pool()
    
    def _init_connection_pool(self):
        """初始化连接池"""
        if settings.vector_db.type == "pgvector":
            # 构建连接字符串，对密码进行URL编码以处理特殊字符（如@符号）
            encoded_password = quote(settings.vector_db.pgvector_password, safe="")
            connection_string = (
                f"postgresql://{settings.vector_db.pgvector_user}:"
                f"{encoded_password}@"
                f"{settings.vector_db.pgvector_host}:"
                f"{settings.vector_db.pgvector_port}/"
                f"{settings.vector_db.pgvector_database}"
            )
            
            # 创建SQLAlchemy引擎，配置连接池
            self.engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=5,  # 连接池大小
                max_overflow=10,  # 最大溢出连接数
                pool_pre_ping=True,  # 连接前ping检查
                pool_recycle=3600,  # 连接回收时间（秒）
                echo=False  # 是否打印SQL语句
            )
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info(f"PGVector连接池已初始化: {settings.vector_db.pgvector_host}:{settings.vector_db.pgvector_port}")
    
    def get_session(self):
        """获取数据库会话"""
        if self.SessionLocal is None:
            raise RuntimeError("连接池未初始化")
        return self.SessionLocal()
    
    def execute_query(self, query: str, params: tuple = None):
        """执行查询并返回结果"""
        session = self.get_session()
        try:
            result = session.execute(text(query), params or {})
            return result.fetchall()
        finally:
            session.close()


class DocumentProcessor:
    """文档处理器，负责文档的加载、分段和向量化"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.file.chunk_size,
            chunk_overlap=settings.file.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # 初始化嵌入模型 - 根据配置选择提供商
        self._init_embeddings()
        
        # 初始化连接池（仅对PGVector）
        self.pgvector_pool = None
        
        # PostgreSQL pgvector连接配置
        print('settings.vector_db.type=============',settings.vector_db.type)
        if settings.vector_db.type == "pgvector":
            # 新版本PGVector使用psycopg3连接字符串
            # 对密码进行URL编码以处理特殊字符（如@符号）
            encoded_password = quote(settings.vector_db.pgvector_password, safe="")
            self.connection_string = (
                f"postgresql+psycopg://{settings.vector_db.pgvector_user}:"
                f"{encoded_password}@"
                f"{settings.vector_db.pgvector_host}:"
                f"{settings.vector_db.pgvector_port}/"
                f"{settings.vector_db.pgvector_database}"
            )
            # 初始化连接池
            self.pgvector_pool = PGVectorConnectionPool()
        else:
            # 向量数据库存储路径（Chroma兼容）
            self.vector_db_path = settings.vector_db.persist_directory
    
    def _init_embeddings(self):
        """根据配置初始化embedding模型"""
        from .embedding_factory import EmbeddingFactory
        self.embeddings = EmbeddingFactory.create_embeddings()
    
    def load_document(self, file_path: str) -> List[Document]:
        """根据文件类型加载文档"""
        file_extension = Path(file_path).suffix.lower()
        
        try:
            if file_extension == '.txt':
                loader = TextLoader(file_path, encoding='utf-8')
                documents = loader.load()
            elif file_extension == '.pdf':
                # 使用pdfplumber处理PDF文件，更稳定
                documents = self._load_pdf_with_pdfplumber(file_path)
            elif file_extension == '.docx':
                loader = Docx2txtLoader(file_path)
                documents = loader.load()
            elif file_extension == '.md':
                loader = UnstructuredMarkdownLoader(file_path)
                documents = loader.load()
            else:
                raise ValueError(f"不支持的文件类型: {file_extension}")
            
            logger.info(f"成功加载文档: {file_path}, 页数: {len(documents)}")
            return documents
            
        except Exception as e:
            logger.error(f"加载文档失败 {file_path}: {str(e)}")
            raise
    
    def _load_pdf_with_pdfplumber(self, file_path: str) -> List[Document]:
        """使用pdfplumber加载PDF文档"""
        documents = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():  # 只处理有文本内容的页面
                        doc = Document(
                            page_content=text,
                            metadata={
                                "source": file_path,
                                "page": page_num + 1
                            }
                        )
                        documents.append(doc)
            return documents
        except Exception as e:
            logger.error(f"使用pdfplumber加载PDF失败 {file_path}: {str(e)}")
            # 如果pdfplumber失败，回退到PyPDFLoader
            try:
                loader = PyPDFLoader(file_path)
                return loader.load()
            except Exception as fallback_e:
                logger.error(f"PyPDFLoader回退也失败 {file_path}: {str(fallback_e)}")
                raise fallback_e
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """将文档分割成小块"""
        try:
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"文档分割完成，共生成 {len(chunks)} 个文档块")
            return chunks
        except Exception as e:
            logger.error(f"文档分割失败: {str(e)}")
            raise
    
    def create_vector_store(self, knowledge_base_id: int, documents: List[Document], document_id: int = None) -> str:
        """为知识库创建向量存储"""
        try:
            if settings.vector_db.type == "pgvector":
                # 添加元数据
                for i, doc in enumerate(documents):
                    doc.metadata.update({
                        "knowledge_base_id": knowledge_base_id,
                        "document_id": str(document_id) if document_id else "unknown",
                        "chunk_id": f"{knowledge_base_id}_{document_id}_{i}",
                        "chunk_index": i
                    })
                
                # 创建PostgreSQL pgvector存储
                collection_name = f"{settings.vector_db.pgvector_table_name}_kb_{knowledge_base_id}"
                
                # 创建新版本PGVector实例
                vector_store = PGVector(
                    connection=self.connection_string,
                    embeddings=self.embeddings,
                    collection_name=collection_name,
                    use_jsonb=True  # 使用JSONB存储元数据
                )
                
                # 手动添加文档
                vector_store.add_documents(documents)
                
                logger.info(f"PostgreSQL pgvector存储创建成功: {collection_name}")
                return collection_name
            else:
                # Chroma兼容模式
                from langchain_community.vectorstores import Chroma
                kb_vector_path = os.path.join(self.vector_db_path, f"kb_{knowledge_base_id}")
                
                # 添加元数据
                for i, doc in enumerate(documents):
                    doc.metadata.update({
                        "knowledge_base_id": knowledge_base_id,
                        "document_id": str(document_id) if document_id else "unknown",
                        "chunk_id": f"{knowledge_base_id}_{document_id}_{i}",
                        "chunk_index": i
                    })
                
                # 创建向量存储
                vector_store = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=kb_vector_path
                )
                
                # 持久化向量存储
                vector_store.persist()
                
                logger.info(f"向量存储创建成功: {kb_vector_path}")
                return kb_vector_path
            
        except Exception as e:
            logger.error(f"创建向量存储失败: {str(e)}")
            raise
    
    def add_documents_to_vector_store(self, knowledge_base_id: int, documents: List[Document], document_id: int = None) -> None:
        """向现有向量存储添加文档"""
        try:
            if settings.vector_db.type == "pgvector":
                # 添加元数据
                for i, doc in enumerate(documents):
                    doc.metadata.update({
                        "knowledge_base_id": knowledge_base_id,
                        "document_id": str(document_id) if document_id else "unknown",
                        "chunk_id": f"{knowledge_base_id}_{document_id}_{i}",
                        "chunk_index": i
                    })

                # PostgreSQL pgvector存储
                collection_name = f"{settings.vector_db.pgvector_table_name}_kb_{knowledge_base_id}"
                try:
                    # 连接到现有集合
                    vector_store = PGVector(
                        connection=self.connection_string,
                        embeddings=self.embeddings,
                        collection_name=collection_name,
                        use_jsonb=True
                    )
                    # 添加新文档
                    vector_store.add_documents(documents)
                except Exception as e:
                    # 如果集合不存在，创建新的向量存储
                    logger.warning(f"连接现有向量存储失败，创建新的向量存储: {e}")
                    self.create_vector_store(knowledge_base_id, documents, document_id)
                    return

                logger.info(f"文档已添加到PostgreSQL pgvector存储: {collection_name}")
            else:
                # Chroma兼容模式
                from langchain_community.vectorstores import Chroma
                kb_vector_path = os.path.join(self.vector_db_path, f"kb_{knowledge_base_id}")
                
                # 检查向量存储是否存在
                if not os.path.exists(kb_vector_path):
                    # 如果不存在，创建新的向量存储
                    self.create_vector_store(knowledge_base_id, documents, document_id)
                    return

                # 添加元数据
                for i, doc in enumerate(documents):
                    doc.metadata.update({
                        "knowledge_base_id": knowledge_base_id,
                        "document_id": str(document_id) if document_id else "unknown",
                        "chunk_id": f"{knowledge_base_id}_{document_id}_{i}",
                        "chunk_index": i
                    })

                # 加载现有向量存储
                vector_store = Chroma(
                    persist_directory=kb_vector_path,
                    embedding_function=self.embeddings
                )

                # 添加新文档
                vector_store.add_documents(documents)
                vector_store.persist()

                logger.info(f"文档已添加到向量存储: {kb_vector_path}")

        except Exception as e:
            logger.error(f"添加文档到向量存储失败: {str(e)}")
            raise
    
    def process_document(self, document_id: int, file_path: str, knowledge_base_id: int) -> Dict[str, Any]:
        """处理单个文档：加载、分段、向量化"""
        try:
            logger.info(f"开始处理文档 ID: {document_id}, 路径: {file_path}")
            
            # 1. 加载文档
            documents = self.load_document(file_path)
            
            # 2. 分割文档
            chunks = self.split_documents(documents)
            
            # 3. 添加到向量存储
            self.add_documents_to_vector_store(knowledge_base_id, chunks, document_id)
            
            # 4. 更新文档状态
            with next(get_db()) as db:
                document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
                if document:
                    document.status = "processed"
                    document.chunk_count = len(chunks)
                    db.commit()
            
            result = {
                "document_id": document_id,
                "status": "success",
                "chunks_count": len(chunks),
                "message": "文档处理完成"
            }
            
            logger.info(f"文档处理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"文档处理失败 ID: {document_id}: {str(e)}")
            
            # 更新文档状态为失败
            try:
                with next(get_db()) as db:
                    document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
                    if document:
                        document.status = "failed"
                        document.error_message = str(e)
                        db.commit()
            except Exception as db_error:
                logger.error(f"更新文档状态失败: {str(db_error)}")
            
            return {
                "document_id": document_id,
                "status": "failed",
                "error": str(e),
                "message": "文档处理失败"
            }
    
    def _get_document_ids_from_vector_store(self, knowledge_base_id: int, document_id: int) -> List[str]:
        """查询指定document_id的所有向量记录的uuid"""
        try:
            collection_name = f"{settings.vector_db.pgvector_table_name}_kb_{knowledge_base_id}"
            
            # 使用连接池执行查询
            if self.pgvector_pool:
                query = f"""
                    SELECT uuid FROM langchain_pg_embedding 
                    WHERE collection_id = (
                        SELECT uuid FROM langchain_pg_collection 
                        WHERE name = %s
                    ) AND cmetadata->>'document_id' = %s
                """
                
                result = self.pgvector_pool.execute_query(query, (collection_name, str(document_id)))
                return [row[0] for row in result] if result else []
            else:
                logger.warning("PGVector连接池未初始化")
                return []
                
        except Exception as e:
            logger.error(f"查询文档向量记录失败: {str(e)}")
            return []
    
    def delete_document_from_vector_store(self, knowledge_base_id: int, document_id: int) -> None:
        """从向量存储中删除文档"""
        try:
            if settings.vector_db.type == "pgvector":
                # PostgreSQL pgvector存储
                collection_name = f"{settings.vector_db.pgvector_table_name}_kb_{knowledge_base_id}"
                
                try:
                    # 创建新版本PGVector实例
                    vector_store = PGVector(
                        connection=self.connection_string,
                        embeddings=self.embeddings,
                        collection_name=collection_name,
                        use_jsonb=True
                    )
                    
                    # 直接从数据库查询要删除的文档UUID
                    try:
                        from sqlalchemy import text
                        from sqlalchemy.orm import Session
                        
                        # 获取数据库引擎
                        engine = vector_store._engine
                        
                        with Session(engine) as session:
                            # 查询匹配document_id的所有记录的ID
                            query_sql = text(
                                f"SELECT id FROM langchain_pg_embedding "
                                f"WHERE cmetadata->>'document_id' = :doc_id"
                            )
                            result = session.execute(query_sql, {"doc_id": str(document_id)})
                            ids_to_delete = [row[0] for row in result.fetchall()]
                        
                        if ids_to_delete:
                            # 使用ID删除文档
                            vector_store.delete(ids=ids_to_delete)
                            logger.info(f"成功删除 {len(ids_to_delete)} 个文档块: document_id={document_id}")
                        else:
                            logger.warning(f"未找到要删除的文档ID: document_id={document_id}")
                            
                    except Exception as query_error:
                        logger.error(f"查询要删除的文档时出错: {query_error}")
                        # 如果查询失败，说明文档可能不存在
                        logger.warning(f"无法查询到要删除的文档: document_id={document_id}")
                        return
                    
                    logger.info(f"文档已从PostgreSQL pgvector存储中删除: document_id={document_id}")
                except Exception as e:
                    logger.warning(f"PostgreSQL pgvector存储不存在或删除失败: {collection_name}, {str(e)}")
            else:
                # Chroma兼容模式
                from langchain_community.vectorstores import Chroma
                kb_vector_path = os.path.join(self.vector_db_path, f"kb_{knowledge_base_id}")
                
                if not os.path.exists(kb_vector_path):
                    logger.warning(f"向量存储不存在: {kb_vector_path}")
                    return
                
                # 加载向量存储
                vector_store = Chroma(
                    persist_directory=kb_vector_path,
                    embedding_function=self.embeddings
                )
                
                # 删除相关文档块（这里需要根据实际的Chroma API来实现）
                # 注意：Chroma的删除功能可能需要特定的实现方式
                logger.info(f"文档已从向量存储中删除: document_id={document_id}")
            
        except Exception as e:
            logger.error(f"从向量存储删除文档失败: {str(e)}")
            raise
    
    def get_document_chunks(self, knowledge_base_id: int, document_id: int) -> List[Dict[str, Any]]:
        """获取文档的所有分段内容
        
        改进说明:
        - 避免使用空查询进行相似性搜索，防止触发不必要的embedding API调用
        - 优先使用直接SQL查询，提高性能
        - 确保结果按chunk_index排序
        """
        try:
            if settings.vector_db.type == "pgvector":
                # PostgreSQL pgvector存储 - 使用直接SQL查询避免相似性搜索
                collection_name = f"{settings.vector_db.pgvector_table_name}_kb_{knowledge_base_id}"
                
                try:
                    # 尝试直接SQL查询（推荐方法）
                    chunks = self._get_chunks_by_sql(knowledge_base_id, document_id)
                    if chunks:
                        return chunks
                    
                    # 如果SQL查询失败，回退到改进的LangChain方法
                    logger.info("SQL查询失败，使用LangChain回退方案")
                    return self._get_chunks_by_langchain_improved(knowledge_base_id, document_id, collection_name)
                    
                except Exception as e:
                    logger.warning(f"PostgreSQL pgvector存储访问失败: {collection_name}, {str(e)}")
                    return []
            else:
                # Chroma兼容模式
                return self._get_chunks_chroma(knowledge_base_id, document_id)
                
        except Exception as e:
            logger.error(f"获取文档分段失败 document_id: {document_id}, kb_id: {knowledge_base_id}: {str(e)}")
            return []
    
    def _get_chunks_by_sql(self, knowledge_base_id: int, document_id: int) -> List[Dict[str, Any]]:
        """使用SQLAlchemy连接池查询获取文档分段（推荐方法）"""
        try:
            if not self.pgvector_pool:
                logger.error("PGVector连接池未初始化")
                return []
            
            # 直接SQL查询，避免相似性搜索和embedding计算
            query = """
                SELECT 
                    id,
                    document,
                    cmetadata
                FROM langchain_pg_embedding 
                WHERE cmetadata->>'document_id' = :document_id
                  AND cmetadata->>'knowledge_base_id' = :knowledge_base_id
                ORDER BY 
                    CAST(cmetadata->>'chunk_index' AS INTEGER) ASC;
            """
            
            # 使用连接池执行查询
            session = self.pgvector_pool.get_session()
            try:
                result = session.execute(
                    text(query), 
                    {
                        'document_id': str(document_id), 
                        'knowledge_base_id': str(knowledge_base_id)
                    }
                )
                results = result.fetchall()
                
                chunks = []
                for row in results:
                    # SQLAlchemy结果行访问
                    metadata = row.cmetadata
                    chunk = {
                        "id": f"chunk_{document_id}_{metadata.get('chunk_index', 0)}",
                        "content": row.document,
                        "metadata": metadata,
                        "page_number": metadata.get("page"),
                        "chunk_index": metadata.get("chunk_index", 0),
                        "start_char": metadata.get("start_char"),
                        "end_char": metadata.get("end_char")
                    }
                    chunks.append(chunk)
                
                logger.info(f"通过SQLAlchemy连接池查询获取到文档 {document_id} 的 {len(chunks)} 个分段")
                return chunks
                
            finally:
                session.close()
            
        except Exception as e:
            logger.error(f"SQLAlchemy连接池查询失败: {e}")
            return []
    
    def _get_chunks_by_langchain_improved(self, knowledge_base_id: int, document_id: int, collection_name: str) -> List[Dict[str, Any]]:
        """改进的LangChain查询方法（回退方案）"""
        try:
            vector_store = PGVector(
                connection=self.connection_string,
                embeddings=self.embeddings,
                collection_name=collection_name,
                use_jsonb=True
            )
            
            # 使用有意义的查询而不是空查询，避免触发embedding API错误
            # 先尝试获取少量结果来构造查询
            try:
                sample_results = vector_store.similarity_search(
                    query="文档内容",  # 使用通用查询词而非空字符串
                    k=5,
                    filter={"document_id": {"$eq": str(document_id)}}
                )
                
                if sample_results:
                    # 使用第一个结果的内容片段作为查询
                    first_content = sample_results[0].page_content[:50]
                    results = vector_store.similarity_search(
                        query=first_content,
                        k=1000,
                        filter={"document_id": {"$eq": str(document_id)}}
                    )
                else:
                    # 如果没有结果，尝试不使用filter的查询
                    results = vector_store.similarity_search(
                        query="文档",
                        k=1000
                    )
                    # 手动过滤结果
                    results = [doc for doc in results if doc.metadata.get("document_id") == str(document_id)]
                
            except Exception as e:
                logger.warning(f"改进的相似性搜索失败: {e}")
                return []
            
            chunks = []
            for i, doc in enumerate(results):
                chunk = {
                    "id": f"chunk_{document_id}_{i}",
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "page_number": doc.metadata.get("page"),
                    "chunk_index": doc.metadata.get("chunk_index", i),
                    "start_char": doc.metadata.get("start_char"),
                    "end_char": doc.metadata.get("end_char")
                }
                chunks.append(chunk)
            
            # 按chunk_index排序
            chunks.sort(key=lambda x: x.get("chunk_index", 0))
            
            logger.info(f"通过改进的LangChain方法获取到文档 {document_id} 的 {len(chunks)} 个分段")
            return chunks
            
        except Exception as e:
            logger.error(f"LangChain改进方法失败: {e}")
            return []
    
    def _get_chunks_chroma(self, knowledge_base_id: int, document_id: int) -> List[Dict[str, Any]]:
        """Chroma存储的处理逻辑"""
        try:
            from langchain_community.vectorstores import Chroma
            
            # 构建向量数据库路径
            vector_db_path = os.path.join(self.vector_db_path, f"kb_{knowledge_base_id}")
            
            if not os.path.exists(vector_db_path):
                logger.warning(f"向量数据库不存在: {vector_db_path}")
                return []
            
            # 加载向量数据库
            vectorstore = Chroma(
                persist_directory=vector_db_path,
                embedding_function=self.embeddings
            )
            
            # 获取所有文档的元数据，筛选出指定文档的分段
            collection = vectorstore._collection
            all_docs = collection.get(include=["metadatas", "documents"])
            
            chunks = []
            chunk_index = 0
            
            for i, metadata in enumerate(all_docs["metadatas"]):
                if metadata.get("document_id") == str(document_id):
                    chunk_content = all_docs["documents"][i]
                    
                    chunk = {
                        "id": f"chunk_{document_id}_{chunk_index}",
                        "content": chunk_content,
                        "metadata": metadata,
                        "page_number": metadata.get("page"),
                        "chunk_index": chunk_index,
                        "start_char": metadata.get("start_char"),
                        "end_char": metadata.get("end_char")
                    }
                    chunks.append(chunk)
                    chunk_index += 1
            
            logger.info(f"获取到文档 {document_id} 的 {len(chunks)} 个分段")
            return chunks
            
        except Exception as e:
            logger.error(f"Chroma存储处理失败: {e}")
            return []
    
    def search_similar_documents(self, knowledge_base_id: int, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """在知识库中搜索相似文档"""
        try:
            if settings.vector_db.type == "pgvector":
                # PostgreSQL pgvector存储
                collection_name = f"{settings.vector_db.pgvector_table_name}_kb_{knowledge_base_id}"
                
                try:
                    vector_store = PGVector(
                        connection=self.connection_string,
                        embeddings=self.embeddings,
                        collection_name=collection_name,
                        use_jsonb=True
                    )
                    
                    # 执行相似性搜索
                    results = vector_store.similarity_search_with_score(query, k=k)
                    
                    # 格式化结果
                    formatted_results = []
                    for doc, distance_score in results:
                        # pgvector使用余弦距离，距离越小相似度越高
                        # 将距离转换为0-1之间的相似度分数
                        similarity_score = 1.0 / (1.0 + distance_score)
                        
                        formatted_results.append({
                            "content": doc.page_content,
                            "metadata": doc.metadata,
                            "similarity_score": distance_score,  # 保留原始距离分数
                            "normalized_score": similarity_score,  # 归一化相似度分数
                            "source": doc.metadata.get('filename', 'unknown'),
                            "document_id": doc.metadata.get('document_id', 'unknown'),
                            "chunk_id": doc.metadata.get('chunk_id', 'unknown')
                        })
                    
                    # 按相似度分数排序（距离越小越相似）
                    formatted_results.sort(key=lambda x: x['similarity_score'])
                    
                    logger.info(f"PostgreSQL pgvector搜索完成，找到 {len(formatted_results)} 个相关文档")
                    return formatted_results
                    
                except Exception as e:
                    logger.warning(f"PostgreSQL pgvector存储不存在: {collection_name}, {str(e)}")
                    return []
            else:
                # Chroma兼容模式
                from langchain_community.vectorstores import Chroma
                kb_vector_path = os.path.join(self.vector_db_path, f"kb_{knowledge_base_id}")
                
                if not os.path.exists(kb_vector_path):
                    logger.warning(f"向量存储不存在: {kb_vector_path}")
                    return []
                
                # 加载向量存储
                vector_store = Chroma(
                    persist_directory=kb_vector_path,
                    embedding_function=self.embeddings
                )
                
                # 执行相似性搜索
                results = vector_store.similarity_search_with_score(query, k=k)
                
                # 格式化结果
                formatted_results = []
                for doc, distance_score in results:
                    # Chroma使用欧几里得距离，距离越小相似度越高
                    # 将距离转换为0-1之间的相似度分数
                    similarity_score = 1.0 / (1.0 + distance_score)
                    
                    formatted_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": distance_score,  # 保留原始距离分数
                        "normalized_score": similarity_score,  # 归一化相似度分数
                        "source": doc.metadata.get('filename', 'unknown'),
                        "document_id": doc.metadata.get('document_id', 'unknown'),
                        "chunk_id": doc.metadata.get('chunk_id', 'unknown')
                    })
                
                # 按相似度分数排序（距离越小越相似）
                formatted_results.sort(key=lambda x: x['similarity_score'])
                
                logger.info(f"搜索完成，找到 {len(formatted_results)} 个相关文档")
                return formatted_results
            
        except Exception as e:
            logger.error(f"搜索文档失败: {str(e)}")
            return []  # 返回空列表而不是抛出异常


# 全局文档处理器实例（延迟初始化）
document_processor = None

def get_document_processor():
    """获取文档处理器实例（延迟初始化）"""
    global document_processor
    if document_processor is None:
        document_processor = DocumentProcessor()
    return document_processor