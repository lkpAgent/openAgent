#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import requests
import json
from pathlib import Path

def get_access_token():
    """获取访问令牌"""
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    response = requests.post(
        "http://localhost:8000/api/auth/login",
        json=login_data
    )
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def test_upload_word():
    """测试上传Word文档"""
    try:
        # 获取访问令牌
        print("获取访问令牌...")
        access_token = get_access_token()
        if not access_token:
            print("无法获取访问令牌，测试终止")
            return
        
        print("✅ 登录成功")
        
        # 创建一个简单的Word文档用于测试
        test_content = """
这是一个测试Word文档。

第一段：这里是一些测试内容，用来验证Word文档的分段功能是否正常工作。这段文字应该被正确地提取和分段。

第二段：文档处理系统应该能够正确地识别和处理Word文档格式，包括文本提取、分段处理和向量化存储。

第三段：这是最后一段测试内容，用来确保整个文档处理流程的完整性和正确性。系统应该能够将这些内容正确地存储到向量数据库中。
        """
        
        # 创建临时Word文档
        from docx import Document
        doc = Document()
        
        # 添加段落
        for paragraph in test_content.strip().split('\n\n'):
            if paragraph.strip():
                doc.add_paragraph(paragraph.strip())
        
        # 保存文档
        test_file = Path("./test_document.docx")
        doc.save(test_file)
        print(f"创建测试文档: {test_file}")
        
        # 上传文档
        print("\n上传文档到知识库...")
        
        # 添加认证头
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        with open(test_file, 'rb') as f:
            files = {'file': ('test_document.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            data = {'process_immediately': 'true'}
            
            response = requests.post(
                'http://localhost:8000/api/knowledge-bases/1/documents',
                files=files,
                data=data,
                headers=headers
            )
            
        if response.status_code == 200:
            result = response.json()
            print(f"上传成功: {result}")
            
            document_id = result.get('document_id')
            if document_id:
                print(f"\n文档ID: {document_id}")
                
                # 等待处理完成
                import time
                print("等待文档处理...")
                time.sleep(5)
                
                # 检查文档分段
                print("\n检查文档分段...")
                chunks_response = requests.get(
                    f'http://localhost:8000/api/knowledge-bases/1/documents/{document_id}/chunks'
                )
                
                if chunks_response.status_code == 200:
                    chunks = chunks_response.json()
                    print(f"分段数量: {len(chunks)}")
                    
                    for i, chunk in enumerate(chunks):
                        print(f"\n分段 {i+1}:")
                        print(f"内容: {chunk.get('content', '')[:200]}...")
                        print(f"页码: {chunk.get('page_number', 'N/A')}")
                else:
                    print(f"获取分段失败: {chunks_response.status_code} - {chunks_response.text}")
        else:
            print(f"上传失败: {response.status_code} - {response.text}")
            
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()
            print(f"\n清理测试文件: {test_file}")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_upload_word()