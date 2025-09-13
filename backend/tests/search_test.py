import os
import sys

# 设置环境变量，必须在导入其他模块之前设置
os.environ['ENV_FILE'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
# 确保数据库配置正确加载
# os.environ['DATABASE_URL'] = 'postgresql://myuser:postgresqlpass2025@113.240.110.92:15432/mydb'

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入所需模块
from open_agent.services.tools import SearchTool
from open_agent.core.config import get_settings

# 重新加载settings以确保获取最新的环境变量
settings = get_settings()
settings.load_from_yaml()
if __name__ == '__main__':
    # 设置Tavily API密钥
    settings.tool.tavily_api_key = "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"
    
    search_tool = SearchTool()
    result = search_tool.execute({"query":"今天的股市"})
    print(result)