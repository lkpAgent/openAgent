#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的文档处理流程，包括智谱AI向量化
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time
from pathlib import Path

def test_document_processing_flow():
    """测试完整的文档处理流程"""
    print("开始测试完整的文档处理流程...")
    
    base_url = "http://localhost:8000"
    
    # 添加认证头
    headers = {
        "Authorization": "Bearer your-secret-key-here-change-in-production",
        "Content-Type": "application/json"
    }
    
    try:
        # 1. 创建知识库
        print("\n1. 创建测试知识库...")
        kb_data = {
            "name": "智谱向量化测试知识库",
            "description": "用于测试智谱AI向量化功能的知识库"
        }
        
        response = requests.post(f"{base_url}/api/knowledge-bases/", json=kb_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ 创建知识库失败: {response.status_code} - {response.text}")
            return False
        
        kb_result = response.json()
        kb_id = kb_result["id"]
        print(f"✅ 知识库创建成功，ID: {kb_id}")
        
        # 2. 创建测试文档
        print("\n2. 创建测试文档...")
        test_content = """智谱AI向量化测试文档

这是一个用于测试智谱AI向量化功能的文档。

智谱AI是一家专注于人工智能技术的公司，提供了强大的语言模型和向量化服务。

本文档包含以下内容：
1. 智谱AI简介
2. 向量化技术原理
3. 应用场景分析

智谱AI的embedding-3模型能够将文本转换为高质量的向量表示，支持语义搜索和相似度计算。

向量化技术在知识库检索、文档相似度匹配、语义搜索等场景中发挥重要作用。

通过本次测试，我们验证了智谱AI向量化接口的稳定性和准确性。"""
        
        test_file_path = Path("test_zhipu_document.txt")
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        print(f"✅ 测试文档创建成功: {test_file_path}")
        
        # 3. 上传文档
        print("\n3. 上传文档到知识库...")
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_zhipu_document.txt", f, "text/plain")}
            data = {"knowledge_base_id": kb_id}
            
            auth_headers = {"Authorization": "Bearer your-secret-key-here-change-in-production"}
            response = requests.post(f"{base_url}/api/documents/upload", files=files, data=data, headers=auth_headers)
        
        if response.status_code != 200:
            print(f"❌ 文档上传失败: {response.status_code} - {response.text}")
            return False
        
        doc_result = response.json()
        doc_id = doc_result["id"]
        print(f"✅ 文档上传成功，ID: {doc_id}")
        
        # 4. 等待文档处理完成
        print("\n4. 等待文档处理完成...")
        max_wait = 30  # 最多等待30秒
        wait_time = 0
        
        while wait_time < max_wait:
            response = requests.get(f"{base_url}/api/documents/{doc_id}", headers=headers)
            if response.status_code == 200:
                doc_info = response.json()
                if doc_info.get("status") == "processed":
                    print("✅ 文档处理完成")
                    break
                elif doc_info.get("status") == "failed":
                    print(f"❌ 文档处理失败: {doc_info.get('error_message', '未知错误')}")
                    return False
            
            time.sleep(2)
            wait_time += 2
            print(f"⏳ 等待中... ({wait_time}s/{max_wait}s)")
        
        if wait_time >= max_wait:
            print("❌ 文档处理超时")
            return False
        
        # 5. 获取文档分段
        print("\n5. 获取文档分段...")
        response = requests.get(f"{base_url}/api/documents/{doc_id}/chunks", headers=headers)
        if response.status_code != 200:
            print(f"❌ 获取文档分段失败: {response.status_code} - {response.text}")
            return False
        
        chunks = response.json()
        print(f"✅ 获取到 {len(chunks)} 个文档分段")
        
        for i, chunk in enumerate(chunks[:3]):  # 只显示前3个分段
            print(f"  分段 {i+1}: {chunk['content'][:100]}...")
        
        # 6. 测试语义搜索
        print("\n6. 测试语义搜索...")
        search_query = "智谱AI向量化技术"
        search_data = {
            "query": search_query,
            "k": 3
        }
        
        response = requests.post(f"{base_url}/api/knowledge-bases/{kb_id}/search", json=search_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ 语义搜索失败: {response.status_code} - {response.text}")
            return False
        
        search_results = response.json()
        print(f"✅ 搜索查询: '{search_query}'")
        print(f"✅ 找到 {len(search_results)} 个相关结果")
        
        for i, result in enumerate(search_results):
            score = result.get('score', 0)
            content = result.get('content', '')[:100]
            print(f"  结果 {i+1} (相似度: {score:.4f}): {content}...")
        
        # 7. 清理测试数据
        print("\n7. 清理测试数据...")
        
        # 删除文档
        response = requests.delete(f"{base_url}/api/documents/{doc_id}", headers=headers)
        if response.status_code == 200:
            print("✅ 测试文档删除成功")
        
        # 删除知识库
        response = requests.delete(f"{base_url}/api/knowledge-bases/{kb_id}", headers=headers)
        if response.status_code == 200:
            print("✅ 测试知识库删除成功")
        
        # 删除本地测试文件
        if test_file_path.exists():
            test_file_path.unlink()
            print("✅ 本地测试文件删除成功")
        
        print("\n🎉 完整的文档处理流程测试成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("智谱AI向量化 - 完整文档处理流程测试")
    print("=" * 60)
    
    success = test_document_processing_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！智谱AI向量化功能正常工作。")
    else:
        print("⚠️  测试失败，请检查系统配置和服务状态。")
    print("=" * 60)