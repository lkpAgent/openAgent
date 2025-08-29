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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)