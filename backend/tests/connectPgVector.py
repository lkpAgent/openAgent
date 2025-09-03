import psycopg2
from sqlalchemy import create_engine, text
from langchain_community.vectorstores.pgvector import PGVector
from langchain_openai import OpenAIEmbeddings
from urllib.parse import quote

# 数据库连接配置（注意密码中的特殊字符需要编码）
DB_CONFIG = {
    "username": "myuser",
    "password": "postgresqlpass@2025",  # 包含特殊字符@
    "host": "113.240.110.92",
    "port": "15432",
    "database": "mydb"
}

# 对密码进行URL编码（关键步骤！）
encoded_password = quote(DB_CONFIG["password"])

# 生成两种连接字符串
PSYCOPG2_CONN_STR = f"""
    dbname='{DB_CONFIG['database']}' 
    user='{DB_CONFIG['username']}' 
    password='{DB_CONFIG['password']}' 
    host='{DB_CONFIG['host']}' 
    port={DB_CONFIG['port']}
"""

SQLALCHEMY_CONN_STR = f"postgresql+psycopg2://{DB_CONFIG['username']}:{encoded_password}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"


def ensure_vector_extension():
    """确保数据库已安装vector扩展"""
    try:
        engine = create_engine(SQLALCHEMY_CONN_STR)
        with engine.connect() as conn:
            # 检查扩展是否存在
            result = conn.execute(text("SELECT 1 FROM pg_extension WHERE extname='vector'"))
            if not result.scalar():
                print("正在创建vector扩展...")
                conn.execute(text("CREATE EXTENSION vector"))
                conn.commit()
                print("vector扩展创建成功")
            else:
                print("vector扩展已存在")
    except Exception as e:
        print(f"创建扩展失败: {type(e).__name__}: {e}")
        raise


def test_connections():
    """测试所有连接方式"""
    print("\n" + "=" * 50)
    print("开始连接测试...")

    # 测试1: 原生psycopg2连接
    try:
        conn = psycopg2.connect(PSYCOPG2_CONN_STR)
        conn.close()
        print("✅ psycopg2直接连接成功")
    except Exception as e:
        print(f"❌ psycopg2连接失败: {type(e).__name__}: {e}")

    # 测试2: SQLAlchemy连接
    try:
        engine = create_engine(SQLALCHEMY_CONN_STR)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ SQLAlchemy连接成功")
    except Exception as e:
        print(f"❌ SQLAlchemy连接失败: {type(e).__name__}: {e}")

    print("=" * 50 + "\n")


def init_vector_store():
    """初始化PGVector存储"""
    embeddings = OpenAIEmbeddings()  # 需要设置OPENAI_API_KEY环境变量

    return PGVector(
        connection_string=SQLALCHEMY_CONN_STR,
        embedding_function=embeddings,
        collection_name="my_documents",
        pre_delete_collection=False,
        engine_args={
            "pool_pre_ping": True,  # 自动检测断连
            "pool_recycle": 3600,  # 每小时重建连接
            "connect_args": {
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 30
            }
        }
    )


if __name__ == "__main__":
    # 步骤1: 验证基础连接
    test_connections()

    # 步骤2: 确保vector扩展存在
    ensure_vector_extension()

    # 步骤3: 初始化向量存储
    try:
        vector_store = init_vector_store()
        print("✅ PGVector初始化成功")

        # 示例操作：添加文档
        docs = ["LangChain很棒", "PostgreSQL是强大的数据库"]
        vector_store.add_texts(docs)
        print(f"已添加 {len(docs)} 个文档")

        # 示例查询
        query = "推荐什么数据库?"
        results = vector_store.similarity_search(query, k=1)
        print(f"查询结果: {results[0].page_content}")

    except Exception as e:
        print(f"❌ PGVector操作失败: {type(e).__name__}: {e}")