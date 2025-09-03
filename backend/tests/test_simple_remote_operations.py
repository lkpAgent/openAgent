#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的远程数据库操作测试
"""

import psycopg2
import json
import uuid
from datetime import datetime

def test_simple_remote_operations():
    """测试简单的远程数据库操作"""
    try:
        print("连接到远程数据库...")
        
        # 直接使用原始密码
        password = "postgresqlpass@2025"
        connection_string = f"host=113.240.110.92 port=15432 dbname=mydb user=myuser password={password}"
        
        # 连接数据库
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
        
        print("✅ 成功连接到远程数据库")
        
        # 检查现有的collection
        print("\n检查现有的collection...")
        cur.execute("SELECT uuid, name FROM langchain_pg_collection;")
        collections = cur.fetchall()
        print(f"找到 {len(collections)} 个collection:")
        for col in collections:
            print(f"  - {col[1]} ({col[0]})")
            
        # 创建或获取测试collection
        test_collection_name = "simple_test_collection"
        cur.execute("SELECT uuid FROM langchain_pg_collection WHERE name = %s;", (test_collection_name,))
        result = cur.fetchone()
        
        if result:
            collection_id = result[0]
            print(f"\n使用现有collection: {collection_id}")
        else:
            collection_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO langchain_pg_collection (uuid, name, cmetadata) VALUES (%s, %s, %s);",
                (collection_id, test_collection_name, json.dumps({}))
            )
            conn.commit()
            print(f"\n创建新collection: {collection_id}")
            
        # 插入测试数据
        print("\n插入测试数据...")
        test_embedding = [0.1] * 2048  # 简单的测试向量
        test_docs = [
            {
                "uuid": str(uuid.uuid4()),
                "collection_id": collection_id,
                "embedding": test_embedding,
                "document": "这是简单测试文档1",
                "cmetadata": {"document_id": "simple_test_1", "source": "simple_test"},
                "custom_id": "simple_test_1"
            },
            {
                "uuid": str(uuid.uuid4()),
                "collection_id": collection_id,
                "embedding": test_embedding,
                "document": "这是简单测试文档2",
                "cmetadata": {"document_id": "simple_test_2", "source": "simple_test"},
                "custom_id": "simple_test_2"
            }
        ]
        
        for doc in test_docs:
            cur.execute(
                "INSERT INTO langchain_pg_embedding (uuid, collection_id, embedding, document, cmetadata, custom_id) VALUES (%s, %s, %s, %s, %s, %s);",
                (doc["uuid"], doc["collection_id"], doc["embedding"], doc["document"], json.dumps(doc["cmetadata"]), doc["custom_id"])
            )
        
        conn.commit()
        print("✅ 测试数据插入成功")
        
        # 查询插入的数据
        print("\n查询插入的数据...")
        cur.execute(
            "SELECT uuid, document, cmetadata FROM langchain_pg_embedding WHERE collection_id = %s;",
            (collection_id,)
        )
        results = cur.fetchall()
        print(f"找到 {len(results)} 条记录:")
        for result in results:
            metadata = result[2] if result[2] else {}
            print(f"  - {result[0]}: {result[1]} (document_id: {metadata.get('document_id')})")
            
        # 测试删除操作
        print("\n测试删除操作...")
        cur.execute(
            "DELETE FROM langchain_pg_embedding WHERE collection_id = %s AND cmetadata->>'document_id' = %s;",
            (collection_id, "simple_test_1")
        )
        deleted_count = cur.rowcount
        conn.commit()
        print(f"✅ 删除了 {deleted_count} 条记录")
        
        # 验证删除结果
        print("\n验证删除结果...")
        cur.execute(
            "SELECT uuid, document, cmetadata FROM langchain_pg_embedding WHERE collection_id = %s;",
            (collection_id,)
        )
        results_after = cur.fetchall()
        print(f"删除后剩余 {len(results_after)} 条记录:")
        for result in results_after:
            metadata = result[2] if result[2] else {}
            print(f"  - {result[0]}: {result[1]} (document_id: {metadata.get('document_id')})")
            
        # 清理测试数据
        print("\n清理测试数据...")
        cur.execute(
            "DELETE FROM langchain_pg_embedding WHERE collection_id = %s;",
            (collection_id,)
        )
        cur.execute(
            "DELETE FROM langchain_pg_collection WHERE uuid = %s;",
            (collection_id,)
        )
        conn.commit()
        print("✅ 测试数据清理完成")
        
        cur.close()
        conn.close()
        
        print("\n🎉 简单远程数据库操作测试成功！")
        return True
        
    except Exception as e:
        print(f"💥 简单远程数据库操作测试失败！")
        print(f"错误详情: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_remote_operations()
    if success:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 测试失败！")