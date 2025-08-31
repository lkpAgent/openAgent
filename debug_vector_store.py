#!/usr/bin/env python3
"""调试向量数据库内容"""

import os
import sys
sys.path.append('backend')

from langchain_community.vectorstores import Chroma
from backend.chat_agent.services.embedding_factory import EmbeddingFactory

def debug_vector_store():
    """调试向量数据库内容"""
    try:
        # 初始化嵌入模型
        embeddings = EmbeddingFactory.create_embeddings()
        
        # 向量数据库路径 - 使用配置中的路径
        vector_db_path = "backend/data/chroma/kb_1"
        
        if not os.path.exists(vector_db_path):
            print(f"❌ 向量数据库不存在: {vector_db_path}")
            return
        
        print(f"✅ 向量数据库存在: {vector_db_path}")
        
        # 加载向量数据库
        vectorstore = Chroma(
            persist_directory=vector_db_path,
            embedding_function=embeddings
        )
        
        # 获取所有文档的元数据
        collection = vectorstore._collection
        all_docs = collection.get(include=["metadatas", "documents"])
        
        print(f"\n📊 向量数据库统计:")
        print(f"总文档数量: {len(all_docs['documents'])}")
        print(f"总元数据数量: {len(all_docs['metadatas'])}")
        
        # 分析元数据
        document_ids = set()
        for i, metadata in enumerate(all_docs["metadatas"]):
            doc_id = metadata.get("document_id")
            document_ids.add(doc_id)
            
            if i < 5:  # 只显示前5个
                print(f"\n📄 文档 {i+1}:")
                print(f"  document_id: {doc_id} (类型: {type(doc_id)})")
                print(f"  knowledge_base_id: {metadata.get('knowledge_base_id')}")
                print(f"  chunk_id: {metadata.get('chunk_id')}")
                print(f"  chunk_index: {metadata.get('chunk_index')}")
                print(f"  内容预览: {all_docs['documents'][i][:100]}...")
        
        # 过滤掉None值再排序
        valid_document_ids = [doc_id for doc_id in document_ids if doc_id is not None]
        print(f"\n🔍 发现的文档ID: {sorted(valid_document_ids)}")
        print(f"🔍 包含None的文档ID: {document_ids}")
        
        # 专门查找文档26
        doc_26_chunks = []
        for i, metadata in enumerate(all_docs["metadatas"]):
            doc_id = metadata.get("document_id")
            if doc_id == "26" or doc_id == 26:
                doc_26_chunks.append({
                    "index": i,
                    "metadata": metadata,
                    "content": all_docs['documents'][i]
                })
        
        print(f"\n🎯 文档26的分段数量: {len(doc_26_chunks)}")
        if len(doc_26_chunks) > 0:
            for chunk in doc_26_chunks[:3]:  # 只显示前3个
                print(f"  分段 {chunk['index']}: {chunk['content'][:100]}...")
                print(f"    元数据: {chunk['metadata']}")
        else:
            print("❌ 没有找到文档26的分段！")
            # 查看所有文档ID，看看是否有类似的
            print("\n🔍 所有文档ID详情:")
            for i, metadata in enumerate(all_docs["metadatas"][:10]):  # 只显示前10个
                doc_id = metadata.get("document_id")
                print(f"  索引{i}: document_id={doc_id} (类型: {type(doc_id)})")
        
    except Exception as e:
        print(f"❌ 调试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_vector_store()