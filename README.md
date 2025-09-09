# ChatAgent - 智能对话与工作流编排平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/vue-3.x-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)](https://www.postgresql.org/)

一个集成了智能对话、知识库管理、智能问数、工作流编排和智能体编排的现代化AI平台，采用Vue.js + FastAPI + PostgreSQL架构，支持本地源码部署。

## ✨ 核心功能

### 🤖 智能问答
- **多模型支持**：集成OpenAI、智谱AI等主流AI服务商
- **三种对话模式**：
  - 自由对话：直接与AI模型交互
  - RAG对话：基于知识库的检索增强生成
  - 智能体对话：多智能体协作处理复杂任务
- **流式响应**：实时显示AI回答过程
- **对话历史**：完整的会话记录和管理

### 📚 知识库管理
- **文档处理**：支持PDF、Word、Markdown、TXT等格式
- **向量存储**：基于PostgreSQL + pgvector的向量数据库
- **智能检索**：语义相似度搜索和精确匹配
- **文档管理**：上传、删除、分类和标签管理
- **RAG集成**：与对话系统无缝集成

### 📊 智能问数
- **Excel分析**：上传Excel文件进行智能数据分析
- **自然语言查询**：用自然语言提问，自动生成Python代码
- **数据库查询**：连接PostgreSQL数据库进行智能查询
- **多表关联**：支持复杂的多表/多文件联合查询

### 🔧 工作流编排
- **可视化设计**：拖拽式工作流设计器
- **节点类型**：支持AI对话、数据处理、条件判断等节点
- **流程控制**：条件分支、循环、并行执行
- **任务调度**：定时执行和事件触发
- **状态监控**：实时查看工作流执行状态

### 🤖 智能体编排
- **多智能体协作**：不同专业领域的AI智能体协同工作
- **角色定义**：自定义智能体的专业能力和知识领域
- **任务分配**：智能分解复杂任务到合适的智能体
- **结果整合**：汇总多个智能体的输出生成最终答案
- **执行监控**：可视化显示智能体工作流程

## 🏗️ 技术架构

### 后端技术栈
- **Web框架**: FastAPI + SQLAlchemy + Alembic
- **数据库**: PostgreSQL 16+
- **向量数据库**: PostgreSQL + pgvector 扩展
- **AI框架**: LangChai/LangGraph + Deepseek/智谱AI/Doubao
- **文档处理**: PyPDF2 + python-docx + markdown
- **数据分析**: Pandas + NumPy 

### 前端技术栈
- **框架**: Vue 3 + TypeScript + Vite
- **UI组件**: Element Plus
- **路由**: Vue Router
- **HTTP客户端**: Axios
- **工作流编辑器**: 自定义可视化编辑器


## 🚀 本地部署指南

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
 

**4. 插入并查询向量数据（示例，可以在客户端，如dbeaver等）**

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

### 3. 后端部署
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


### 4. 前端部署
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
 

### 6. 访问应用
- 前端地址: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## ⚙️ 配置说明

### 后端环境变量配置 (backend/.env)

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

### 前端环境变量配置 (.env)

```env
# API配置
VITE_API_BASE_URL=http://localhost:8000/api




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
│   ├── public/             # 静态资源
│   └── package.json        # Node.js依赖
├── data/                   # 数据目录
│   ├── uploads/            # 上传文件
│   └── logs/               # 日志文件
└── docs/                   # 文档目录
```

### 添加新功能

#### 后端开发
1. 在 `chat_agent/api/endpoints/` 添加新的路由
2. 在 `chat_agent/services/` 添加业务逻辑
3. 在 `chat_agent/utils/schemas.py` 定义数据模型
4. 在 `tests/` 添加测试用例

#### 前端开发
1. 在 `src/components/` 或 `src/views/` 添加组件
2. 在 `src/api/` 添加API调用函数
3. 在 `src/types/` 定义TypeScript类型
4. 在 `src/router/` 添加路由配置

### 开发工具

#### 代码格式化
```bash
# 后端代码格式化
cd backend
black chat_agent/
isort chat_agent/
flake8 chat_agent/

# 前端代码格式化
cd frontend
npm run lint
npm run format
```

#### 类型检查
```bash
# 后端类型检查
cd backend
mypy chat_agent/

# 前端类型检查
cd frontend
npm run type-check
```

### 测试

#### 后端测试
```bash
cd backend
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_chat.py -v

# 生成覆盖率报告
pytest tests/ --cov=chat_agent --cov-report=html
```

#### 前端测试
```bash
cd frontend
# 运行单元测试
npm run test:unit

# 运行E2E测试
npm run test:e2e

# 生成覆盖率报告
npm run test:coverage
```

## 🔍 故障排除

### 常见问题

#### 1. PostgreSQL连接失败

**Docker方式：**
```bash
# 检查Docker容器状态
docker ps | grep pgvector-db

# 查看容器日志
docker logs pgvector-db

# 重启容器
docker restart pgvector-db

# 检查端口是否被占用
netstat -an | grep 5432
```

**本地安装方式：**
```bash
# 检查PostgreSQL服务状态
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# 检查端口是否被占用
netstat -an | grep 5432
```

#### 2. pgvector扩展未安装

**Docker方式：**
```bash
# 进入容器检查扩展
docker exec -it pgvector-db psql -U myuser -d mydb -c "\dx"

# 如果未安装，进入容器安装
docker exec -it pgvector-db psql -U myuser -d mydb -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**本地安装方式：**
```sql
-- 检查扩展是否已安装
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 如果未安装，执行安装
CREATE EXTENSION vector;
```

#### 3. Redis连接失败
```bash
# 检查Redis服务状态
redis-cli ping

# 启动Redis服务
sudo systemctl start redis  # Linux
brew services start redis  # macOS
```

#### 4. 前端构建失败
```bash
# 清理node_modules和重新安装
rm -rf node_modules package-lock.json
npm install

# 检查Node.js版本
node --version  # 需要18+
```

### 日志查看

#### 后端日志
```bash
# 查看应用日志
tail -f ./logs/app.log

# 查看数据库日志
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

#### 前端日志
```bash
# 开发模式下查看控制台输出
npm run dev

# 构建时查看详细输出
npm run build -- --verbose
```

## 🤝 贡献指南

### 开发流程
1. Fork项目到个人仓库
2. 创建功能分支: `git checkout -b feature/new-feature`
3. 提交代码: `git commit -m 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 创建Pull Request

### 代码规范
- 后端遵循PEP 8规范
- 前端遵循Vue 3 + TypeScript最佳实践
- 提交信息遵循Conventional Commits规范

### 测试要求
- 新功能必须包含单元测试
- 测试覆盖率不低于80%
- 所有测试必须通过

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 🙏 致谢

感谢以下开源项目的支持：
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [PostgreSQL](https://www.postgresql.org/) - 强大的开源数据库
- [pgvector](https://github.com/pgvector/pgvector) - PostgreSQL向量扩展
- [LangChain](https://langchain.com/) - AI应用开发框架

特别感谢：
- [Fivk博客](https://blog.fivk.cn/archives/6626.html) - 提供了详细的Docker安装PostgreSQL + pgvector教程

---

**如果这个项目对你有帮助，请给它一个 ⭐️！**