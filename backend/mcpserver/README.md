# MCP服务器

统一的MCP工具服务HTTP REST API服务器，提供数据库连接和查询功能。

## 功能特性

- 🚀 统一的HTTP REST API接口
- 🔧 支持MySQL和PostgreSQL数据库
- 📊 工具管理和生命周期控制
- 🔍 健康检查和监控
- 📝 完整的API文档
- 🛡️ 错误处理和日志记录

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务器

#### 方式一：使用Python脚本
```bash
python start_server.py
```

#### 方式二：使用批处理脚本 (Windows)
```bash
start_server.bat
```

#### 方式三：使用命令行参数
```bash
python main.py --host 0.0.0.0 --port 8001 --enable-mysql --enable-postgresql
```

### 3. 访问API文档

启动后访问：http://localhost:8001/docs

## API接口

### 基础接口

- `GET /` - 服务信息
- `GET /health` - 健康检查
- `GET /tools` - 获取工具列表
- `GET /tools/{tool_name}` - 获取工具信息
- `POST /execute` - 执行工具

### MySQL专用接口

- `POST /mysql/connect` - 连接MySQL数据库
- `POST /mysql/query` - 执行MySQL查询

### PostgreSQL专用接口

- `POST /postgresql/connect` - 连接PostgreSQL数据库
- `POST /postgresql/query` - 执行PostgreSQL查询

## 使用示例

### 连接MySQL数据库

```bash
curl -X POST "http://localhost:8001/mysql/connect" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_config": {
      "host": "localhost",
      "port": 3306,
      "database": "test",
      "username": "root",
      "password": "password"
    },
    "user_id": "user123"
  }'
```

### 执行查询

```bash
curl -X POST "http://localhost:8001/mysql/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "sql_query": "SELECT * FROM users LIMIT 10",
    "limit": 10
  }'
```

## 配置选项

### 环境变量

- `MCP_HOST` - 服务器主机地址 (默认: 0.0.0.0)
- `MCP_PORT` - 服务器端口 (默认: 8001)
- `MCP_LOG_LEVEL` - 日志级别 (默认: INFO)

### 命令行参数

```bash
python main.py --help
```

- `--host` - 服务器主机地址
- `--port` - 服务器端口
- `--reload` - 启用自动重载 (开发模式)
- `--enable-mysql` - 启用MySQL工具
- `--enable-postgresql` - 启用PostgreSQL工具
- `--log-level` - 日志级别

## 目录结构

```
mcpserver/
├── __init__.py          # 包初始化
├── config.py            # 配置管理
├── manager.py           # 服务管理器
├── api.py              # HTTP API接口
├── main.py             # 主启动文件
├── start_server.py     # 快速启动脚本
├── start_server.bat    # Windows启动脚本
├── requirements.txt    # 依赖包列表
├── README.md          # 说明文档
└── tools/             # 工具目录
    ├── __init__.py
    ├── mysql_mcp.py    # MySQL工具
    └── postgresql_mcp.py # PostgreSQL工具
```

## 开发指南

### 添加新工具

1. 在 `tools/` 目录下创建新的工具文件
2. 继承 `BaseTool` 类并实现必要方法
3. 在 `tools/__init__.py` 中导入新工具
4. 在 `config.py` 中添加工具配置
5. 在 `manager.py` 中注册新工具

### 自定义配置

修改 `config.py` 文件中的 `MCPServerConfig` 类来自定义配置。

## 故障排除

### 常见问题

1. **端口被占用**
   - 使用 `--port` 参数指定其他端口
   - 或者停止占用端口的进程

2. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证连接配置是否正确
   - 确认网络连接是否正常

3. **导入错误**
   - 确保已安装所有依赖包
   - 检查Python路径配置

### 日志查看

服务器运行时会输出详细的日志信息，包括：
- 启动信息
- 工具加载状态
- API请求日志
- 错误信息

## 许可证

本项目遵循MIT许可证。