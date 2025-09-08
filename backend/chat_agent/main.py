from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add backend directory to Python path for direct execution
if __name__ == "__main__":
    backend_dir = Path(__file__).parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file
load_dotenv()

from chat_agent.core.app import create_app

# Create FastAPI application using factory function
app = create_app()

# 在 main.py 中添加表元数据路由



if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description='ChatAgent Backend Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    
    args = parser.parse_args()
    
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)