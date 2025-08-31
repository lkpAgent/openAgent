#!/usr/bin/env python3
"""
测试文档分段功能
测试支持的文档格式：TXT、PDF、Word、Excel等
"""

import os
import sys
import requests
import json
import time
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent / "backend"))

# API配置
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "123456"

def login_and_get_token():
    """登录并获取访问令牌"""
    # 使用与test_api_direct.py相同的方式
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent / "backend"))
    
    from chat_agent.db.database import get_db_session
    from chat_agent.services.auth import AuthService
    
    try:
        # 直接调用API函数
        db = get_db_session()
        auth_service = AuthService()
        
        user = auth_service.authenticate_user_by_email(db, TEST_EMAIL, TEST_PASSWORD)
        if user:
            access_token = auth_service.create_access_token(data={"sub": user.email})
            print(f"✅ 直接API登录成功!")
            print(f"用户: {user.username} ({user.email})")
            return access_token
        else:
            print("❌ 用户认证失败")
            return None
    except Exception as e:
        print(f"❌ 登录过程出错: {e}")
        return None
    finally:
        if 'db' in locals():
            db.close()

def create_test_knowledge_base(token):
    """创建测试知识库"""
    print(f"使用token: {token[:50]}...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    kb_data = {
        "name": "文档分段测试知识库",
        "description": "用于测试各种文档格式的分段功能"
    }
    
    response = requests.post(
        f"{BASE_URL}/knowledge-bases/",
        json=kb_data,
        headers=headers
    )
    
    if response.status_code == 200:
        kb = response.json()
        print(f"创建知识库成功: {kb['name']} (ID: {kb['id']})")
        return kb["id"]
    else:
        print(f"创建知识库失败: {response.status_code} - {response.text}")
        return None

def create_test_files():
    """创建测试文件"""
    test_files = {}
    
    # 创建TXT文件
    txt_content = """这是一个测试文档。

第一段：人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

第二段：机器学习是人工智能的一个重要分支，它通过算法使计算机能够从数据中学习并做出决策或预测，而无需被明确编程。

第三段：深度学习是机器学习的一个子集，它模仿人脑的神经网络结构，通过多层神经网络来学习数据的复杂模式。

第四段：自然语言处理（NLP）是人工智能的另一个重要领域，它致力于让计算机理解、解释和生成人类语言。"""
    
    txt_file = "test_document.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(txt_content)
    test_files["txt"] = txt_file
    
    # 创建Markdown文件
    md_content = """# 测试文档

## 第一章 人工智能概述

人工智能（Artificial Intelligence，AI）是计算机科学的一个分支。

### 1.1 定义

AI企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

### 1.2 发展历程

- 1950年：图灵测试提出
- 1956年：达特茅斯会议，AI正式诞生
- 1980年代：专家系统兴起
- 2010年代：深度学习突破

## 第二章 机器学习

机器学习是人工智能的一个重要分支。

### 2.1 监督学习

通过标记数据训练模型。

### 2.2 无监督学习

从未标记数据中发现模式。

### 2.3 强化学习

通过与环境交互学习最优策略。
"""
    
    md_file = "test_document.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    test_files["md"] = md_file
    
    return test_files

def upload_document(token, kb_id, file_path):
    """上传文档"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"knowledge_base_id": str(kb_id)}
        
        response = requests.post(
            f"{BASE_URL}/knowledge-bases/{kb_id}/documents",
            files=files,
            data=data,
            headers=headers
        )
    
    if response.status_code == 200:
        doc = response.json()
        print(f"上传文档成功: {doc['filename']} (ID: {doc['id']})")
        return doc
    else:
        print(f"上传文档失败: {response.status_code} - {response.text}")
        return None

def wait_for_processing(token, kb_id, doc_id, max_wait=60):
    """等待文档处理完成"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = requests.get(
            f"{BASE_URL}/knowledge-bases/{kb_id}/documents",
            headers=headers
        )
        
        if response.status_code == 200:
            docs_data = response.json()
            documents = docs_data.get("documents", docs_data) if isinstance(docs_data, dict) else docs_data
            
            for doc in documents:
                if doc["id"] == doc_id:
                    status = doc["status"]
                    print(f"文档状态: {status}")
                    
                    if status == "processed":
                        return True
                    elif status == "failed":
                        print("文档处理失败")
                        return False
        
        time.sleep(2)
    
    print("等待处理超时")
    return False

def get_document_chunks(token, kb_id, doc_id):
    """获取文档分段"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/knowledge-bases/{kb_id}/documents/{doc_id}/chunks",
        headers=headers
    )
    
    if response.status_code == 200:
        chunks_data = response.json()
        chunks = chunks_data.get("chunks", chunks_data) if isinstance(chunks_data, dict) else chunks_data
        print(f"获取到 {len(chunks)} 个文档分段")
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n分段 {i}:")
            print(f"内容长度: {len(chunk.get('content', ''))} 字符")
            print(f"内容预览: {chunk.get('content', '')[:100]}...")
            if chunk.get('metadata'):
                print(f"元数据: {chunk['metadata']}")
        
        return chunks
    else:
        print(f"获取文档分段失败: {response.status_code} - {response.text}")
        return []

def cleanup_files(files):
    """清理测试文件"""
    for file_path in files.values():
        try:
            os.remove(file_path)
            print(f"删除测试文件: {file_path}")
        except Exception as e:
            print(f"删除文件失败 {file_path}: {e}")

def get_knowledge_bases(token):
    """获取现有知识库列表"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}/knowledge-bases/",
        headers=headers
    )
    
    if response.status_code == 200:
        kb_list = response.json()
        print(f"获取到 {len(kb_list)} 个知识库")
        for kb in kb_list:
            print(f"  - {kb['name']} (ID: {kb['id']})")
        return kb_list
    else:
        print(f"获取知识库列表失败: {response.status_code} - {response.text}")
        return []

def cleanup_test_data(token, kb_id, test_files):
    """清理测试数据"""
    # 清理测试文件
    cleanup_files(test_files)
    print("测试数据清理完成")

def main():
    """主测试函数"""
    print("开始测试文档分段功能...")
    
    # 1. 登录
    print("\n1. 登录系统...")
    token = login_and_get_token()
    if not token:
        print("登录失败，测试终止")
        return
    
    print(f"Token长度: {len(token)}")
    print(f"Token前50字符: {token[:50]}...")
    
    # 2. 获取现有知识库列表
    print("\n2. 获取现有知识库...")
    kb_list = get_knowledge_bases(token)
    if not kb_list:
        print("获取知识库列表失败，尝试创建新知识库")
        kb_id = create_test_knowledge_base(token)
        if not kb_id:
            print("创建知识库失败，测试终止")
            return
    else:
        # 使用第一个知识库
        kb_id = kb_list[0]['id']
        print(f"使用现有知识库: {kb_list[0]['name']} (ID: {kb_id})")
    
    try:
        # 3. 创建测试文件
        print("\n3. 创建测试文件...")
        test_files = create_test_files()
        
        # 4. 测试各种格式的文档
        print("\n4. 测试文档上传和分段...")
        
        for file_type, file_path in test_files.items():
            print(f"\n--- 测试 {file_type.upper()} 格式 ---")
            
            # 上传文档
            doc = upload_document(token, kb_id, file_path)
            if not doc:
                continue
            
            # 等待处理完成
            print("等待文档处理...")
            if wait_for_processing(token, kb_id, doc["id"]):
                # 获取分段内容
                chunks = get_document_chunks(token, kb_id, doc["id"])
                if chunks:
                    print(f"✅ {file_type.upper()} 格式文档分段成功")
                else:
                    print(f"❌ {file_type.upper()} 格式文档分段失败")
            else:
                print(f"❌ {file_type.upper()} 格式文档处理失败")
        
        print("\n✅ 文档分段功能测试完成！")
        
    finally:
        # 5. 清理
        print("\n5. 清理测试数据...")
        cleanup_test_data(token, kb_id, test_files)

if __name__ == "__main__":
    main()