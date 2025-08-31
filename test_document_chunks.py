#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文档分段功能的API调用
测试流程：
1. 创建知识库
2. 上传PDF文档
3. 检查文档处理状态
4. 获取文档分段内容
"""

import requests
import time
import json
import os
from pathlib import Path

# API基础URL
BASE_URL = "http://localhost:8000"

# 测试用户凭据
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "123456"

def login_and_get_token():
    """登录并获取访问令牌"""
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=headers)
    if response.status_code == 200:
        token_info = response.json()
        return token_info.get("access_token")
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def get_auth_headers(token):
    """获取带有认证令牌的请求头"""
    return {"Authorization": f"Bearer {token}"}

def test_document_chunks():
    """测试文档分段功能"""
    print("=== 开始测试文档分段功能 ===")
    
    # 0. 登录获取令牌
    print("\n0. 用户登录...")
    token = login_and_get_token()
    if not token:
        print("登录失败，无法继续测试")
        return False
    
    headers = get_auth_headers(token)
    print("登录成功，获取到访问令牌")
    
    # 1. 创建知识库
    print("\n1. 创建知识库...")
    kb_data = {
        "name": "测试知识库",
        "description": "用于测试文档分段功能的知识库"
    }
    
    response = requests.post(f"{BASE_URL}/api/knowledge-bases", json=kb_data, headers=headers)
    if response.status_code != 200:
        print(f"创建知识库失败: {response.status_code} - {response.text}")
        return False
    
    kb_info = response.json()
    kb_id = kb_info["id"]
    print(f"知识库创建成功，ID: {kb_id}")
    
    # 2. 上传PDF文档
    print("\n2. 上传PDF文档...")
    pdf_path = Path("backend/docs/外骨骼机械腿的设计与研究.pdf")
    
    if not pdf_path.exists():
        print(f"PDF文件不存在: {pdf_path}")
        return False
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        data = {'process_immediately': 'true'}
        
        response = requests.post(
            f"{BASE_URL}/api/knowledge-bases/{kb_id}/documents",
            files=files,
            data=data,
            headers=headers
        )
    
    if response.status_code != 200:
        print(f"文档上传失败: {response.status_code} - {response.text}")
        return False
    
    doc_info = response.json()
    doc_id = doc_info["id"]
    print(f"文档上传成功，ID: {doc_id}")
    print(f"文档状态: {doc_info.get('status', 'unknown')}")
    
    # 3. 等待文档处理完成
    print("\n3. 等待文档处理完成...")
    max_wait_time = 60  # 最大等待60秒
    wait_interval = 3   # 每3秒检查一次
    
    for i in range(0, max_wait_time, wait_interval):
        response = requests.get(f"{BASE_URL}/api/knowledge-bases/{kb_id}/documents/{doc_id}", headers=headers)
        if response.status_code == 200:
            doc_status = response.json()
            status = doc_status.get('status', 'unknown')
            chunk_count = doc_status.get('chunk_count', 0)
            
            print(f"第{i//wait_interval + 1}次检查 - 状态: {status}, 分段数: {chunk_count}")
            
            if status == 'processed' and chunk_count > 0:
                print("文档处理完成！")
                break
            elif status == 'failed':
                print("文档处理失败！")
                return False
        
        if i < max_wait_time - wait_interval:
            time.sleep(wait_interval)
    else:
        print("等待超时，文档可能仍在处理中")
    
    # 4. 获取文档分段内容
    print("\n4. 获取文档分段内容...")
    response = requests.get(f"{BASE_URL}/api/knowledge-bases/{kb_id}/documents/{doc_id}/chunks", headers=headers)
    
    if response.status_code != 200:
        print(f"获取分段失败: {response.status_code} - {response.text}")
        return False
    
    chunks = response.json()
    print(f"成功获取 {len(chunks)} 个文档分段")
    
    # 显示前3个分段的内容预览
    for i, chunk in enumerate(chunks[:3]):
        content = chunk.get('content', '')[:200]  # 只显示前200个字符
        print(f"\n分段 {i+1} (前200字符):")
        print(f"内容: {content}...")
        print(f"页码: {chunk.get('metadata', {}).get('page', 'unknown')}")
    
    if len(chunks) > 3:
        print(f"\n... 还有 {len(chunks) - 3} 个分段")
    
    # 5. 测试搜索功能
    print("\n5. 测试相似性搜索...")
    search_data = {
        "query": "外骨骼",
        "k": 3
    }
    
    response = requests.post(f"{BASE_URL}/api/knowledge-bases/{kb_id}/search", json=search_data, headers=headers)
    
    if response.status_code == 200:
        search_results = response.json()
        print(f"搜索到 {len(search_results)} 个相关分段")
        
        for i, result in enumerate(search_results):
            content = result.get('content', '')[:150]
            score = result.get('score', 0)
            print(f"结果 {i+1} (相似度: {score:.3f}): {content}...")
    else:
        print(f"搜索失败: {response.status_code} - {response.text}")
    
    print("\n=== 测试完成 ===")
    return True

def check_api_health():
    """检查API服务是否正常"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    # 检查API服务状态
    if not check_api_health():
        print("错误: API服务不可用，请确保后端服务正在运行")
        print(f"请检查 {BASE_URL} 是否可访问")
        exit(1)
    
    # 运行测试
    success = test_document_chunks()
    
    if success:
        print("\n✅ 测试成功！文档分段功能正常工作")
    else:
        print("\n❌ 测试失败！请检查错误信息")