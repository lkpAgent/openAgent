#!/usr/bin/env python3
"""测试文档上传和分段功能"""

import requests
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "backend"))

# 切换到backend目录，确保使用相同的数据库
os.chdir(str(Path(__file__).parent / "backend"))

from chat_agent.db.database import get_db_session
from chat_agent.services.auth import AuthService
from chat_agent.models.user import User
from chat_agent.models.knowledge_base import KnowledgeBase, Document
from chat_agent.utils.schemas import DocumentChunk

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """获取认证token"""
    db = get_db_session()
    try:
        # 查找demo用户
        user = db.query(User).filter(User.username == "demo").first()
        if not user:
            print("❌ Demo用户不存在")
            return None
        
        # 创建token
        token_data = {"sub": user.username}
        token = AuthService.create_access_token(token_data)
        print(f"✅ Token: {token[:50]}...")
        return token
    finally:
        db.close()

def test_document_upload_and_segmentation():
    """测试文档上传和分段功能"""
    print("开始测试文档上传和分段功能...")
    
    # 获取认证token
    token = get_auth_token()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 1. 获取知识库列表
    print("\n1. 获取知识库列表...")
    response = requests.get(f"{BASE_URL}/api/knowledge-bases/", headers=headers)
    print(f"状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 获取知识库失败: {response.text}")
        return
    
    knowledge_bases = response.json()
    print(f"✅ 找到 {len(knowledge_bases)} 个知识库")
    
    if not knowledge_bases:
        print("❌ 没有可用的知识库")
        return
    
    kb_id = knowledge_bases[0]['id']
    kb_name = knowledge_bases[0]['name']
    print(f"使用知识库: {kb_name} (ID: {kb_id})")
    
    # 2. 创建测试文档内容
    test_content = """这是一个测试文档，用于验证文档分段功能。

第一段：人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。

第二段：机器学习是人工智能的一个重要分支，它是一种通过算法使机器能够从数据中学习并做出决策或预测的方法。机器学习算法通过训练数据来构建数学模型，以便对新的、未见过的数据做出预测或决策。

第三段：深度学习是机器学习的一个子集，它基于人工神经网络，特别是深层神经网络。深度学习在图像识别、语音识别、自然语言处理等领域取得了突破性进展，成为当前人工智能发展的重要推动力。

第四段：自然语言处理（Natural Language Processing，NLP）是人工智能和语言学领域的分支学科。它研究能实现人与计算机之间用自然语言进行有效通信的各种理论和方法。NLP是计算机科学领域与人工智能领域中的一个重要方向。"""
    
    # 创建临时测试文件
    test_file_path = "test_document.txt"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)
    
    try:
        # 3. 上传文档
        print("\n2. 上传测试文档...")
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_document.txt", f, "text/plain")}
            data = {"knowledge_base_id": kb_id}
            response = requests.post(
                f"{BASE_URL}/api/knowledge-bases/{kb_id}/documents",
                headers=headers,
                files=files,
                data={"process_immediately": "true"}
            )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ 文档上传失败: {response.text}")
            return
        
        upload_result = response.json()
        document_id = upload_result['id']
        print(f"✅ 文档上传成功，ID: {document_id}")
        print(f"文档信息: {upload_result['filename']} ({upload_result['file_size']} bytes)")
        
        # 4. 检查数据库中的文档分段
        print("\n3. 检查文档分段...")
        db = get_db_session()
        try:
            # 查询文档
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                print("❌ 数据库中未找到文档")
                return
            
            print(f"✅ 文档处理状态: {'已处理' if document.is_processed else '未处理'}")
            print(f"文档路径: {document.file_path}")
            
            print(f"文档分段数量: {document.chunk_count}")
            
            if document.chunk_count == 0:
                print("❌ 文档没有被分段！")
                # 如果文档没有被处理，尝试手动触发处理
                if not document.is_processed:
                    print("尝试手动触发文档处理...")
                    process_response = requests.post(
                        f"{BASE_URL}/api/knowledge-bases/{kb_id}/documents/{document_id}/process",
                        headers=headers
                    )
                    print(f"处理请求状态码: {process_response.status_code}")
                    if process_response.status_code == 200:
                        print("✅ 文档处理请求已发送")
                        # 等待处理完成
                        import time
                        print("等待文档处理完成...")
                        time.sleep(5)  # 等待5秒
                        
                        # 重新查询文档状态
                        document = db.query(Document).filter(Document.id == document_id).first()
                        if document:
                            print(f"✅ 更新后的文档处理状态: {'已处理' if document.is_processed else '未处理'}")
                            print(f"文档分段数量: {document.chunk_count}")
                            if document.chunk_count > 0:
                                print("✅ 文档已成功分段！")
                            else:
                                print("❌ 文档仍未分段")
                                if document.processing_error:
                                    print(f"处理错误: {document.processing_error}")
                    else:
                        print(f"❌ 文档处理请求失败: {process_response.text}")
                        return
                else:
                    return
            
            # 5. 通过API获取文档分段
            print("\n4. 通过API获取文档分段...")
            response = requests.get(
                f"{BASE_URL}/api/knowledge-bases/{kb_id}/documents/{document_id}/chunks",
                headers=headers
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ 获取文档分段失败: {response.text}")
                return
            
            api_result = response.json()
            api_chunks = api_result.get('chunks', [])
            print(f"✅ API返回 {len(api_chunks)} 个分段")
            
            # 显示分段详情
            for i, chunk in enumerate(api_chunks, 1):
                print(f"\n分段 {i}:")
                print(f"  - ID: {chunk['id']}")
                print(f"  - 序号: {chunk['chunk_index']}")
                print(f"  - 内容长度: {len(chunk['content'])} 字符")
                print(f"  - 内容预览: {chunk['content'][:100]}...")
                if chunk.get('metadata'):
                    print(f"  - 元数据: {chunk['metadata']}")
            
            # 验证分段数量与数据库一致
            if len(api_chunks) == document.chunk_count:
                print("✅ API分段数量与数据库一致")
            else:
                print(f"❌ API分段数量({len(api_chunks)})与数据库({document.chunk_count})不一致")
            
            # 6. 测试文档列表API
            print("\n5. 测试文档列表API...")
            response = requests.get(
                f"{BASE_URL}/api/knowledge-bases/{kb_id}/documents",
                headers=headers
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"API响应数据类型: {type(response_data)}")
                print(f"API响应内容: {response_data}")
                
                # 检查响应格式
                if isinstance(response_data, dict) and 'documents' in response_data:
                    documents = response_data['documents']
                elif isinstance(response_data, list):
                    documents = response_data
                else:
                    print(f"❌ 未知的响应格式: {response_data}")
                    return
                    
                print(f"✅ 知识库包含 {len(documents)} 个文档")
                
                # 查找我们刚上传的文档
                uploaded_doc = next((doc for doc in documents if doc['id'] == document_id), None)
                if uploaded_doc:
                    print(f"✅ 找到上传的文档: {uploaded_doc['filename']}")
                    print(f"文档处理状态: {'已处理' if uploaded_doc['is_processed'] else '未处理'}")
                    print(f"文档分段数量: {uploaded_doc['chunk_count']}")
                else:
                    print("❌ 文档列表中未找到上传的文档")
            else:
                print(f"❌ 获取文档列表失败: {response.text}")
            
            print("\n🎉 文档上传和分段功能测试完成！")
            
        finally:
            db.close()
    
    finally:
        # 清理临时文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == "__main__":
    test_document_upload_and_segmentation()