#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from chat_agent.services.document_processor import document_processor
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_word_processing():
    """测试Word文档处理"""
    try:
        # 查找最近上传的Word文档
        upload_dir = Path("./data/uploads")
        
        # 查找所有.docx文件
        word_files = list(upload_dir.glob("**/*.docx"))
        
        if not word_files:
            print("没有找到Word文档")
            return
            
        # 处理最新的Word文档
        latest_word = max(word_files, key=lambda f: f.stat().st_mtime)
        print(f"找到最新的Word文档: {latest_word}")
        
        # 测试文档加载
        print("\n1. 测试文档加载...")
        documents = document_processor.load_document(str(latest_word))
        print(f"加载成功，文档数量: {len(documents)}")
        
        if documents:
            print(f"第一个文档内容长度: {len(documents[0].page_content)}")
            print(f"内容预览: {documents[0].page_content[:200]}...")
            
            # 测试文档分段
            print("\n2. 测试文档分段...")
            chunks = document_processor.split_documents(documents)
            print(f"分段成功，分段数量: {len(chunks)}")
            
            if chunks:
                print(f"第一个分段内容长度: {len(chunks[0].page_content)}")
                print(f"分段预览: {chunks[0].page_content[:200]}...")
                
                # 测试向量化（不实际存储）
                print("\n3. 测试向量化...")
                try:
                    # 只测试一个分段的向量化
                    test_text = chunks[0].page_content
                    embedding = document_processor.embeddings.embed_query(test_text)
                    print(f"向量化成功，向量维度: {len(embedding)}")
                except Exception as e:
                    print(f"向量化失败: {e}")
            else:
                print("分段结果为空")
        else:
            print("文档加载结果为空")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_word_processing()