#!/usr/bin/env python3
"""手动触发文档26的处理"""

import requests
import json

def get_access_token():
    """获取访问令牌"""
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    response = requests.post("http://localhost:8000/api/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def manual_process_document():
    """手动处理文档26"""
    try:
        # 获取访问令牌
        print("获取访问令牌...")
        token = get_access_token()
        if not token:
            return
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 首先检查文档26是否存在
        print("\n检查文档26是否存在...")
        response = requests.get("http://localhost:8000/api/knowledge-bases/1/documents", headers=headers)
        if response.status_code == 200:
            docs_data = response.json()
            documents = docs_data.get("documents", docs_data) if isinstance(docs_data, dict) else docs_data
            
            doc_26 = None
            for doc in documents:
                if doc["id"] == 26:
                    doc_26 = doc
                    break
            
            if doc_26:
                print(f"✅ 找到文档26: {doc_26['filename']}")
                print(f"   文件路径: {doc_26['file_path']}")
                print(f"   是否已处理: {doc_26['is_processed']}")
                print(f"   分段数量: {doc_26['chunk_count']}")
                print(f"   文件大小: {doc_26['file_size']} bytes")
                
                # 检查文件是否存在
                import os
                file_path = doc_26['file_path']
                full_file_path = os.path.join('backend', file_path)
                if os.path.exists(full_file_path):
                    print(f"✅ 文件存在: {full_file_path}")
                else:
                    print(f"❌ 文件不存在: {full_file_path}")
                    return
                
            else:
                print("❌ 文档26不存在")
                return
        else:
            print(f"❌ 获取文档列表失败: {response.status_code} - {response.text}")
            return
        
        # 手动触发文档处理
        print("\n手动触发文档26处理...")
        response = requests.post(
            "http://localhost:8000/api/knowledge-bases/1/documents/26/process",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 处理请求成功: {result}")
        else:
            print(f"❌ 处理请求失败: {response.status_code} - {response.text}")
            
        # 等待处理完成并检查结果
        import time
        print("\n等待处理完成...")
        time.sleep(5)
        
        # 重新检查文档状态
        response = requests.get("http://localhost:8000/api/knowledge-bases/1/documents", headers=headers)
        if response.status_code == 200:
            docs_data = response.json()
            documents = docs_data.get("documents", docs_data) if isinstance(docs_data, dict) else docs_data
            
            for doc in documents:
                if doc["id"] == 26:
                    print(f"\n📊 处理后的文档26状态:")
                    print(f"   是否已处理: {doc['is_processed']}")
                    print(f"   分段数量: {doc['chunk_count']}")
                    if 'processing_error' in doc and doc['processing_error']:
                        print(f"   处理错误: {doc['processing_error']}")
                    break
        
        # 尝试获取分段
        print("\n尝试获取文档26的分段...")
        response = requests.get(
            "http://localhost:8000/api/knowledge-bases/1/documents/26/chunks",
            headers=headers
        )
        
        if response.status_code == 200:
            chunks_data = response.json()
            chunks = chunks_data.get("chunks", chunks_data) if isinstance(chunks_data, dict) else chunks_data
            print(f"✅ 获取到 {len(chunks)} 个分段")
            
            for i, chunk in enumerate(chunks[:3]):  # 只显示前3个
                print(f"  分段 {i+1}: {chunk.get('content', '')[:100]}...")
        else:
            print(f"❌ 获取分段失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    manual_process_document()