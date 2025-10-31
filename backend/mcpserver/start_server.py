#!/usr/bin/env python3
"""MCP服务器快速启动脚本"""

import os
import sys
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
sys.path.insert(0, str(backend_dir))

from mcpserver.main import main

if __name__ == "__main__":
    # 设置环境变量
    os.environ.setdefault("PYTHONPATH", str(backend_dir))
    
    # 启动服务器
    main()