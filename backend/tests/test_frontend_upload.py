#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
import requests
import json
from pathlib import Path
from io import BytesIO

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_frontend_document_upload():
    """测试通过前端API上传文档"""
    try:
        base_url = "http://localhost:8000"
        
        # 1. 登录获取token
        logger.info("1. 登录获取访问令牌...")
        login_data = {
            "email": "demo@example.com",
            "password": "123456"
        }
        
        login_response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            logger.error(f"登录失败: {login_response.status_code} - {login_response.text}")
            return False
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        logger.info("✅ 登录成功")
        
        # 2. 获取知识库列表
        logger.info("2. 获取知识库列表...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        kb_response = requests.get(
            f"{base_url}/api/knowledge-bases/",
            headers=headers
        )
        
        if kb_response.status_code != 200:
            logger.error(f"获取知识库失败: {kb_response.status_code} - {kb_response.text}")
            return False
        
        knowledge_bases = kb_response.json()
        if not knowledge_bases:
            logger.error("没有找到知识库")
            return False
        
        kb_id = knowledge_bases[0]["id"]
        logger.info(f"✅ 找到知识库 ID: {kb_id}")
        
        # 3. 创建测试文档
        logger.info("3. 创建测试文档...")
        test_content = """人工智能技术发展报告

第一章：人工智能概述
人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

第二章：机器学习基础
机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习。机器学习算法通过分析数据来识别模式，并使用这些模式来做出预测或决策。

第三章：深度学习技术
深度学习是机器学习的一个子集，它使用人工神经网络来模拟人脑的工作方式。深度学习在图像识别、自然语言处理和语音识别等领域取得了突破性进展。

第四章：应用前景
人工智能技术在医疗、金融、交通、教育等各个领域都有广泛的应用前景，将为人类社会带来深刻的变革。"""
        
        # 4. 通过API上传文档
        logger.info("4. 通过API上传文档...")
        
        # 创建文件对象
        test_file = BytesIO(test_content.encode('utf-8'))
        
        files = {
            'file': ('ai_report.txt', test_file, 'text/plain')
        }
        data = {
            'process_immediately': 'true'
        }
        
        upload_response = requests.post(
            f"{base_url}/api/knowledge-bases/{kb_id}/documents",
            headers={"Authorization": f"Bearer {access_token}"},
            files=files,
            data=data
        )
        
        logger.info(f"上传状态码: {upload_response.status_code}")
        logger.info(f"响应内容: {upload_response.text}")
        
        if upload_response.status_code == 200:
            result = upload_response.json()
            document_id = result.get('id')
            logger.info(f"✅ 文档上传成功，文档ID: {document_id}")
            
            # 5. 等待处理完成
            import time
            logger.info("5. 等待文档处理完成...")
            time.sleep(3)
            
            # 6. 检查文档状态
            logger.info("6. 检查文档处理状态...")
            status_response = requests.get(
                f"{base_url}/api/knowledge-bases/{kb_id}/documents/{document_id}",
                headers=headers
            )
            
            if status_response.status_code == 200:
                doc_info = status_response.json()
                logger.info(f"文档处理状态: {'已处理' if doc_info.get('is_processed') else '未处理'}")
                logger.info(f"分段数量: {doc_info.get('chunk_count', 0)}")
                
                if doc_info.get('processing_error'):
                    logger.error(f"处理错误: {doc_info['processing_error']}")
                    return False
                
                # 7. 测试搜索功能
                logger.info("7. 测试搜索功能...")
                search_response = requests.get(
                    f"{base_url}/api/knowledge-bases/{kb_id}/search",
                    params={"query": "人工智能", "limit": 3},
                    headers=headers
                )
                
                if search_response.status_code == 200:
                    search_results = search_response.json()
                    logger.info(f"✅ 搜索成功，找到 {len(search_results.get('results', []))} 个结果")
                    
                    for i, result in enumerate(search_results.get('results', [])):
                        logger.info(f"  结果 {i+1}: 相似度={result.get('score', 0):.4f}")
                        content_preview = result.get('content', '')[:50]
                        logger.info(f"    内容预览: {content_preview}...")
                else:
                    logger.error(f"搜索失败: {search_response.status_code} - {search_response.text}")
                    return False
                
                # 8. 清理测试数据
                logger.info("8. 清理测试数据...")
                delete_response = requests.delete(
                    f"{base_url}/api/knowledge-bases/{kb_id}/documents/{document_id}",
                    headers=headers
                )
                
                if delete_response.status_code == 200:
                    logger.info("✅ 测试数据清理完成")
                else:
                    logger.warning(f"清理测试数据失败: {delete_response.status_code}")
                
                return True
            else:
                logger.error(f"获取文档状态失败: {status_response.status_code} - {status_response.text}")
                return False
        else:
            logger.error(f"❌ 文档上传失败: {upload_response.status_code} - {upload_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("开始前端文档上传API测试...")
    
    success = test_frontend_document_upload()
    if success:
        print("\n✅ 前端文档上传API测试通过！向量创建功能正常工作。")
    else:
        print("\n❌ 前端文档上传API测试失败！")
        sys.exit(1)