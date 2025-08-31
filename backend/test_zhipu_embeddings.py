#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智谱AI向量化配置
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_agent.services.embedding_factory import EmbeddingFactory
import requests
import json

def test_zhipu_embeddings():
    """测试智谱AI向量化接口"""
    print("开始测试智谱AI向量化接口...")
    
    # 初始化智谱AI嵌入模型
    embeddings = EmbeddingFactory.create_embeddings()
    
    # 测试文本
    test_text = "你好，今天天气怎么样。"
    
    try:
        # 测试单个查询嵌入
        print(f"测试文本: {test_text}")
        embedding = embeddings.embed_query(test_text)
        print(f"嵌入向量维度: {len(embedding)}")
        print(f"嵌入向量前5个值: {embedding[:5]}")
        
        # 测试批量文档嵌入
        test_docs = [
            "这是第一个测试文档。",
            "这是第二个测试文档，内容稍有不同。",
            "第三个文档包含更多的技术内容。"
        ]
        
        print("\n测试批量文档嵌入...")
        doc_embeddings = embeddings.embed_documents(test_docs)
        print(f"批量嵌入结果数量: {len(doc_embeddings)}")
        
        for i, doc_embedding in enumerate(doc_embeddings):
            print(f"文档 {i+1} 嵌入向量维度: {len(doc_embedding)}")
            print(f"文档 {i+1} 嵌入向量前3个值: {doc_embedding[:3]}")
        
        print("\n✅ 智谱AI向量化配置测试成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 智谱AI向量化配置测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_api():
    """直接测试智谱AI API接口"""
    print("\n直接测试智谱AI API接口...")
    
    url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
    headers = {
        "Authorization": "Bearer 864f980a5cf2b4ff16e1bb47beae15d0.gS1t9iDYqmETy1R2",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "embedding-3",
        "input": "你好，今天天气怎么样。"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        print(f"API响应状态: {response.status_code}")
        print(f"嵌入向量维度: {len(result['data'][0]['embedding'])}")
        print(f"嵌入向量前5个值: {result['data'][0]['embedding'][:5]}")
        print("✅ 直接API调用测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ 直接API调用测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("智谱AI向量化配置测试")
    print("=" * 50)
    
    # 测试直接API调用
    api_success = test_direct_api()
    
    # 测试封装的嵌入类
    embedding_success = test_zhipu_embeddings()
    
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print(f"直接API调用: {'✅ 成功' if api_success else '❌ 失败'}")
    print(f"嵌入类封装: {'✅ 成功' if embedding_success else '❌ 失败'}")
    
    if api_success and embedding_success:
        print("\n🎉 所有测试通过！智谱AI向量化配置正常工作。")
    else:
        print("\n⚠️  部分测试失败，请检查配置。")
    print("=" * 50)