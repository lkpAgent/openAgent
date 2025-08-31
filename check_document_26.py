#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import requests
import json
import time

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

def check_document_status():
    """检查文档26的状态"""
    try:
        # 获取访问令牌
        print("获取访问令牌...")
        access_token = get_access_token()
        if not access_token:
            print("无法获取访问令牌，检查终止")
            return
        
        print("✅ 登录成功")
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        document_id = 26
        
        # 检查文档状态
        print(f"\n检查文档 {document_id} 的状态...")
        doc_response = requests.get(
            f"http://localhost:8000/api/knowledge-bases/1/documents/{document_id}",
            headers=headers
        )
        
        if doc_response.status_code == 200:
            doc_info = doc_response.json()
            print(f"文档信息:")
            print(f"  文件名: {doc_info.get('original_filename')}")
            print(f"  文件大小: {doc_info.get('file_size_mb')} MB")
            print(f"  是否已处理: {doc_info.get('is_processed')}")
            print(f"  分段数量: {doc_info.get('chunk_count')}")
            print(f"  处理错误: {doc_info.get('processing_error')}")
            print(f"  向量化模型: {doc_info.get('embedding_model')}")
            
            # 如果文档未处理，等待一段时间再检查
            if not doc_info.get('is_processed'):
                print("\n文档尚未处理完成，等待10秒后再次检查...")
                time.sleep(10)
                
                # 再次检查
                doc_response = requests.get(
                    f"http://localhost:8000/api/knowledge-bases/1/documents/{document_id}",
                    headers=headers
                )
                
                if doc_response.status_code == 200:
                    doc_info = doc_response.json()
                    print(f"\n更新后的文档状态:")
                    print(f"  是否已处理: {doc_info.get('is_processed')}")
                    print(f"  分段数量: {doc_info.get('chunk_count')}")
                    print(f"  处理错误: {doc_info.get('processing_error')}")
            
            # 检查文档分段
            print(f"\n检查文档 {document_id} 的分段...")
            chunks_response = requests.get(
                f"http://localhost:8000/api/knowledge-bases/1/documents/{document_id}/chunks",
                headers=headers
            )
            
            if chunks_response.status_code == 200:
                chunks = chunks_response.json()
                print(f"分段数量: {len(chunks) if isinstance(chunks, list) else 'unknown'}")
                print(f"Chunks类型: {type(chunks)}")
                print(f"Chunks内容预览: {str(chunks)[:500]}...")
                
                if chunks:
                    # 如果chunks是字典，需要获取实际的分段列表
                    if isinstance(chunks, dict):
                        chunk_list = chunks.get('chunks', chunks.get('data', []))
                        print(f"从字典中提取的分段列表长度: {len(chunk_list) if isinstance(chunk_list, list) else 'not a list'}")
                    else:
                        chunk_list = chunks
                        print(f"直接使用chunks作为列表，长度: {len(chunk_list)}")
                    
                    if isinstance(chunk_list, list) and chunk_list:
                        for i, chunk in enumerate(chunk_list[:3]):  # 只显示前3个分段
                            print(f"\n分段 {i+1}:")
                            print(f"  分段类型: {type(chunk)}")
                            print(f"  分段内容: {chunk}")
                            if isinstance(chunk, dict):
                                print(f"  内容: {chunk.get('content', '')[:200]}...")
                                print(f"  页码: {chunk.get('page_number', 'N/A')}")
                                print(f"  字符数: {len(chunk.get('content', ''))}")
                    else:
                        print(f"chunk_list不是列表或为空: {chunk_list}")
                else:
                    print("没有找到分段内容")
            else:
                print(f"获取分段失败: {chunks_response.status_code} - {chunks_response.text}")
                
        else:
            print(f"获取文档信息失败: {doc_response.status_code} - {doc_response.text}")
            
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_document_status()