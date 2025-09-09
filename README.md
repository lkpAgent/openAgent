# ChatAgent - 企业级智能对话与工作流编排平台


🚀 **完全开源的企业级大模型应用平台** - 集成智能问答、智能问数、知识库、工作流和智能体编排的大模型解决方案。采用Vue.js + FastAPI + PostgreSQL+Langchain/LangGraph架构，专为企业级应用设计，代码完全开源，支持私有化部署，可灵活扩展及二次开发。



## ✨ 核心功能



### 🤖 智能问答

![智能问答界面](docs/images/smart_qa.png)

- **多模型支持**：集成DeepSeek、智谱AI、豆包等国内主流AI服务商
- **三种对话模式**：
  - 自由对话：直接与AI模型交互
  - RAG对话：基于知识库的检索增强生成
  - 智能体对话：多智能体协作处理复杂任务
- **多轮对话**：支持连续对话，上下文理解和记忆
- **对话历史**：完整的会话记录和管理

### 📊 智能问数

![智能问数界面](docs/images/smart_data.png)

- **Excel分析**：上传Excel文件进行智能数据分析
- **自然语言查询**：用自然语言提问，自动生成Python代码
- **数据库查询**：连接PostgreSQL等数据库进行智能问答
- **多表关联**：支持复杂的多表/多文件联合查询
- **可视化思维链**：大模型思考过程可视化呈现

### 📚 知识库管理

![知识库管理界面](docs/images/knowledge_base.png)

- **文档处理**：支持PDF、Word、Markdown、TXT等格式
- **向量存储**：基于PostgreSQL + pgvector的向量数据库
- **智能检索**：语义相似度搜索和精确匹配
- **文档管理**：上传、删除、分类和标签管理
- **RAG集成**：与对话系统无缝集成

### 🔧 工作流编排

![工作流编排界面](docs/images/workflow.png)

- **可视化设计**：拖拽式工作流设计器
- **节点类型**：支持AI对话、数据处理、条件判断等节点
- **流程控制**：条件分支、循环、并行执行

### 🤖 智能体编排
- **多智能体协作**：不同专业领域的AI智能体协同工作
- **角色定义**：自定义智能体的专业能力和知识领域
- **任务分配**：智能分解复杂任务到合适的智能体
- **结果整合**：汇总多个智能体的输出生成最终答案

## 🏗️ 技术架构



### 后端技术栈
- **Web框架**: FastAPI + SQLAlchemy + Alembic
- **数据库**: PostgreSQL 16+ (开源关系型数据库)
- **向量数据库**: PostgreSQL + pgvector 扩展 (开源向量数据库)
- **AI框架**: LangChain/LangGraph + 多模型支持
- **文档处理**: PyPDF2 + python-docx + markdown
- **数据分析**: Pandas + NumPy
- **容器化**: Docker + Docker Compose

### 前端技术栈
- **框架**: Vue 3 + TypeScript + Vite
- **UI组件**: Element Plus (开源UI库)
- **路由**: Vue Router
- **HTTP客户端**: Axios
- **工作流编辑器**: 自研可视化编辑器
- **工作流引擎**: 基于DAG的流程执行引擎
- **图形渲染**: Canvas API + SVG
- **拖拽交互**: Vue Draggable
- **节点连接**: 自定义连线算法



## 本地部署指南


### 环境要求
- Python 3.10+
- Node.js 18+
- PostgreSQL 16+

### 1. 安装PostgreSQL和pgvector

#### 方式一：Docker安装（推荐）
使用 Docker + Docker Compose 部署 PostgreSQL 16 + pgvector 插件。

**1. 创建docker-compose.yml文件**

内容如下：

```yaml
version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg16
    container_name: pgvector-db
    environment:
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: your_password
      POSTGRES_DB: mydb
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  pgdata:
```

**说明：**
- 使用 `pgvector/pgvector:pg16` 镜像，内置 PostgreSQL 16 + pgvector 插件
- 数据保存在 Docker 卷 `pgdata` 中，重启不会丢失
- 监听宿主机端口 5432，可用本地工具如 pgAdmin, DBeaver, psql 连接
- 默认数据库名称：mydb
- 默认用户名：myuser
- 默认密码：your_password

**2. 启动服务**

在 `docker-compose.yml` 所在目录下运行：
```bash
docker-compose up -d
```

查看容器状态：
```bash
docker ps
```

输出应包含一个名为 `pgvector-db` 的容器，状态为 Up。

**3. 验证 pgvector 安装成功**

进入 PostgreSQL 容器：
```bash
docker exec -it pgvector-db psql -U myuser -d mydb
```

启用 pgvector 插件：
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
 
插入并查询向量数据（示例，可以在客户端，如dbeaver等）**

```sql
-- 创建表，包含一个向量字段（维度为3）
CREATE TABLE items (
  id SERIAL PRIMARY KEY,
  embedding vector(3)
);

-- 插入向量数据
INSERT INTO items (embedding) VALUES
  ('[1,1,1]'),
  ('[2,2,2]'),
  ('[1,0,0]');

-- 查询与 [1,1,1] 最接近的向量（基于欧几里得距离）
SELECT id, embedding
FROM items
ORDER BY embedding <-> '[1,1,1]'
LIMIT 3;
```
-- 上述没报错且有结果返回，即安装成功

### 2. 后端部署
```bash
# 克隆项目
git clone https://github.com/lkpAgent/chat-agent.git
cd chat-agent/backend

#创建python虚拟环境，推荐使用conda创建虚拟环境
conda create -n chat-agent python=3.10
conda activate chat-agent

# 安装依赖
pip install -r requirements.txt

# 配置环境变量,windows下直接复制.env.example文件为.env  
cp .env.example .env

# 编辑.env文件，配置数据库连接和AI API密钥。相关配置信息见后面的配置说明

# 配置完数据库信息后，初始化数据库表及创建登录账号(用户名: test, 密码: 123456)
cd backend/tests
python init_db.py

# 启动后端服务，默认8000端口
python -m uvicorn chat_agent.main:app --reload --host 0.0.0.0 --port 8000
# 或者直接运行main.py
# cd backend/chat_agent
# python main.py

```


### 3. 前端部署
```bash
# 进入前端目录
cd ../frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑.env文件，配置后端API地址
VITE_API_BASE_URL = http://localhost:8000

# 启动前端服务，默认端口3000
npm run dev
```
 

### 4. 访问应用
- 前端地址: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 5. 后端配置说明

#### 后端环境变量配置 (backend/.env)

```env

# 数据库配置
# ========================================
DATABASE_URL=postgresql://your_username:your_password@your_host:your_port/your_db
# 示例：
# DATABASE_URL=postgresql://myuser:mypassword@127.0.0.1:5432/mydb

# ========================================
# 向量数据库配置
# ========================================
VECTOR_DB_TYPE=pgvector
PGVECTOR_HOST=your_host
PGVECTOR_PORT=your_port
PGVECTOR_DATABASE=mydb
PGVECTOR_USER=myuser
PGVECTOR_PASSWORD=your_password
 
# 大模型配置 (支持OpenAI协议的第三方服务) 只需要配置一种chat大模型以及embedding大模型
# ========================================
# chat大模型配置
# ========================================
# 可选择的提供商: openai, deepseek, doubao, zhipu, moonshot
LLM_PROVIDER=doubao

# Embedding模型配置
# ========================================
# 可选择的提供商: openai, deepseek, doubao, zhipu, moonshot
EMBEDDING_PROVIDER=zhipu

# OpenAI配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002


# 智谱AI配置
ZHIPU_API_KEY=your-zhipu-api-key
ZHIPU_MODEL=glm-4
ZHIPU_EMBEDDING_MODEL=embedding-3
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# DeepSeek配置
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_EMBEDDING_MODEL=deepseek-embedding

# 豆包配置
DOUBAO_API_KEY=your-doubao-api-key
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL=doubao-1-5-pro-32k-250115
DOUBAO_EMBEDDING_MODEL=doubao-embedding

# Moonshot配置
MOONSHOT_API_KEY=your-moonshot-api-key
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
MOONSHOT_MODEL=moonshot-v1-8k
MOONSHOT_EMBEDDING_MODEL=moonshot-embedding


```


## 📖 API文档

### 主要API端点

#### 认证相关
- `POST /auth/login` - 用户登录
- `POST /auth/register` - 用户注册
- `POST /auth/refresh` - 刷新Token

#### 对话管理
- `GET /chat/conversations` - 获取对话列表
- `POST /chat/conversations` - 创建新对话
- `POST /chat/conversations/{id}/chat` - 发送消息

#### 知识库管理
- `POST /knowledge/upload` - 上传文档
- `GET /knowledge/documents` - 获取文档列表
- `DELETE /knowledge/documents/{id}` - 删除文档

#### 智能查询
- `POST /smart-query/query` - 智能数据查询
- `POST /smart-query/upload` - 上传Excel文件
- `GET /smart-query/files` - 获取文件列表

### 完整API文档
启动后端服务后访问: http://localhost:8000/docs

## 🔧 开发指南

### 项目结构
```
chat-agent/
├── backend/                 # 后端代码
│   ├── chat_agent/         # 主应用包
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── db/             # 数据库相关
│   │   ├── models/         # 数据库模型
│   │   ├── services/       # 业务逻辑
│   │   ├── utils/          # 工具函数
│   │   └── main.py         # 应用入口
│   ├── tests/              # 测试文件
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # Vue组件
│   │   ├── views/          # 页面组件
│   │   │   ├── chat/       # 对话页面
│   │   │   ├── knowledge/  # 知识库页面
│   │   │   ├── workflow/   # 工作流页面
│   │   │   └── agent/      # 智能体页面
│   │   ├── stores/         # Pinia状态管理
│   │   ├── api/            # API调用
│   │   ├── types/          # TypeScript类型
│   │   └── router/         # 路由配置
│   └── package.json        # Node.js依赖
├── data/                   # 数据目录
│   ├── uploads/            # 上传文件
│   └── logs/               # 日志文件
└── docs/                   # 文档目录
```


### 测试

#### 后端测试
```bash
cd backend/tests

# 运行特定测试
pytest test_chat.py -v

```




#### 💼 商业使用
- ✅ 可用于商业项目
- ✅ 可修改源码
- ✅ 可私有化部署
- ✅ 可集成到现有系统
- ✅ 无需支付许可费用

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证，这意味着：
- 可以自由使用、修改、分发
- 可以用于商业目的
- 只需保留原始许可证声明
- 作者不承担任何责任

## 🙏 致谢



**如果这个项目对你有帮助，请给它一个 ⭐️！**