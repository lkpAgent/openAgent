#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查远程数据库表结构
"""

import psycopg2
from urllib.parse import quote

def check_remote_db_structure():
    """检查远程数据库表结构"""
    try:
        print("连接到远程数据库...")
        
        # 直接使用原始密码
        password = "postgresqlpass@2025"
        connection_string = f"host=113.240.110.92 port=15432 dbname=mydb user=myuser password={password}"
        
        # 连接数据库
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
        
        print("✅ 成功连接到远程数据库")
        
        # 检查是否存在pgvector扩展
        print("\n检查pgvector扩展...")
        cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        vector_ext = cur.fetchall()
        if vector_ext:
            print("✅ pgvector扩展已安装")
        else:
            print("❌ pgvector扩展未安装")
            
        # 列出所有表
        print("\n列出所有表...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        print(f"找到 {len(tables)} 个表:")
        for table in tables:
            print(f"  - {table[0]}")
            
        # 检查langchain相关表
        print("\n检查langchain相关表...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%langchain%'
            ORDER BY table_name;
        """)
        langchain_tables = cur.fetchall()
        if langchain_tables:
            print(f"找到 {len(langchain_tables)} 个langchain表:")
            for table in langchain_tables:
                print(f"  - {table[0]}")
                
                # 查看表结构
                print(f"\n表 {table[0]} 的结构:")
                cur.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = '{table[0]}'
                    ORDER BY ordinal_position;
                """)
                columns = cur.fetchall()
                for col in columns:
                    print(f"    {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        else:
            print("❌ 未找到langchain相关表")
            
        cur.close()
        conn.close()
        print("\n✅ 数据库结构检查完成")
        return True
        
    except Exception as e:
        print(f"💥 数据库结构检查失败！")
        print(f"错误详情: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_remote_db_structure()
    if success:
        print("\n🎉 远程数据库结构检查完成！")
    else:
        print("\n💥 远程数据库结构检查失败！")