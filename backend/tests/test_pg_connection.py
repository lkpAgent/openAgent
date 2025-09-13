import sys
import os
from pathlib import Path
import logging
import psycopg2
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from open_agent.core.config import Settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_postgresql_connection():
    """测试PostgreSQL基础连接"""
    try:
        logger.info("开始测试PostgreSQL连接...")
        
        # 加载配置
        config_path = Path(__file__).parent / "configs" / "settings.yaml"
        settings = Settings.load_from_yaml(str(config_path))
        
        # 显示连接信息
        logger.info(f"连接信息:")
        logger.info(f"  主机: {settings.vector_db.pgvector_host}")
        logger.info(f"  端口: {settings.vector_db.pgvector_port}")
        logger.info(f"  数据库: {settings.vector_db.pgvector_database}")
        logger.info(f"  用户: {settings.vector_db.pgvector_user}")
        
        # 构建连接字符串
        connection_string = f"postgresql://{settings.vector_db.pgvector_user}:{settings.vector_db.pgvector_password}@{settings.vector_db.pgvector_host}:{settings.vector_db.pgvector_port}/{settings.vector_db.pgvector_database}"
        
        logger.info("尝试连接PostgreSQL...")
        
        # 测试基础连接
        conn = psycopg2.connect(
            host=settings.vector_db.pgvector_host,
            port=settings.vector_db.pgvector_port,
            database=settings.vector_db.pgvector_database,
            user=settings.vector_db.pgvector_user,
            password=settings.vector_db.pgvector_password
        )
        
        logger.info("✅ PostgreSQL连接成功")
        
        # 测试数据库版本
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"PostgreSQL版本: {version}")
        
        # 检查pgvector扩展
        logger.info("检查pgvector扩展...")
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        extension_result = cursor.fetchall()
        
        if extension_result:
            logger.info("✅ pgvector扩展已安装")
            for ext in extension_result:
                logger.info(f"  扩展信息: {ext}")
        else:
            logger.warning("⚠️ pgvector扩展未安装")
            
            # 尝试安装pgvector扩展
            logger.info("尝试安装pgvector扩展...")
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
                logger.info("✅ pgvector扩展安装成功")
            except Exception as e:
                logger.error(f"❌ pgvector扩展安装失败: {e}")
                return False
        
        # 测试向量操作
        logger.info("测试基础向量操作...")
        try:
            # 创建测试表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_vectors (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    embedding VECTOR(3)
                );
            """)
            conn.commit()
            logger.info("✅ 测试向量表创建成功")
            
            # 插入测试向量
            cursor.execute("""
                INSERT INTO test_vectors (content, embedding) 
                VALUES ('test', '[1,2,3]')
                ON CONFLICT DO NOTHING;
            """)
            conn.commit()
            logger.info("✅ 测试向量插入成功")
            
            # 查询测试向量
            cursor.execute("SELECT * FROM test_vectors LIMIT 1;")
            result = cursor.fetchone()
            logger.info(f"✅ 测试向量查询成功: {result}")
            
            # 清理测试表
            cursor.execute("DROP TABLE IF EXISTS test_vectors;")
            conn.commit()
            logger.info("✅ 测试表清理完成")
            
        except Exception as e:
            logger.error(f"❌ 向量操作测试失败: {e}")
            return False
        
        cursor.close()
        conn.close()
        logger.info("✅ 连接已关闭")
        
        return True
        
    except psycopg2.OperationalError as e:
        logger.error(f"❌ PostgreSQL连接失败: {e}")
        logger.error("请检查:")
        logger.error("  1. PostgreSQL服务是否运行")
        logger.error("  2. 主机地址和端口是否正确")
        logger.error("  3. 数据库名称是否存在")
        logger.error("  4. 用户名和密码是否正确")
        logger.error("  5. 防火墙是否允许连接")
        return False
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始PostgreSQL连接测试...")
    
    success = test_postgresql_connection()
    if success:
        print("\n✅ PostgreSQL连接测试通过！")
        print("数据库连接正常，pgvector扩展可用")
    else:
        print("\n❌ PostgreSQL连接测试失败！")
        print("请检查数据库配置和网络连接")
        sys.exit(1)