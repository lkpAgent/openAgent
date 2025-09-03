#!/usr/bin/env python3
"""测试前端API端点的文档上传功能"""

import requests
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_document_upload_api():
    """测试文档上传API端点"""
    base_url = "http://localhost:8000"
    
    try:
        # 1. 登录获取token
        logger.info("1. 登录获取访问令牌...")
        login_data = {
            "email": "demo@example.com",
            "password": "123456"
        }
        
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            logger.error(f"登录失败: {login_response.status_code} - {login_response.text}")
            return False
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("✅ 登录成功")
        
        # 2. 测试文档上传API
        logger.info("2. 测试文档上传API...")
        
        # 检查文件是否存在
        file_path = "docs/custom_tool_guide.md"
        if not os.path.exists(file_path):
            logger.error(f"测试文件不存在: {file_path}")
            return False
            
        # 上传文档
        with open(file_path, 'rb') as f:
            files = {'file': ('custom_tool_guide.md', f, 'text/markdown')}
            
            upload_response = requests.post(
                f"{base_url}/api/knowledge-bases/1/documents",
                headers=headers,
                files=files
            )
            
        logger.info(f"上传响应状态码: {upload_response.status_code}")
        logger.info(f"上传响应内容: {upload_response.text}")
        
        if upload_response.status_code == 200:
            logger.info("✅ 文档上传成功")
            return True
        else:
            logger.error(f"❌ 文档上传失败: {upload_response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_document_upload_api()
    if success:
        print("\n✅ API端点测试通过！")
    else:
        print("\n❌ API端点测试失败！")