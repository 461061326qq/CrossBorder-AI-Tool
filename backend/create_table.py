# create_table.py（修改后）
import os
import psycopg2

def create_tables():
    # 从环境变量获取数据库URL
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set!")
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # ✅ 确保所有表都使用 IF NOT EXISTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL
        )
    """)
    
    # 添加其他表...
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            price NUMERIC(10,2) NOT NULL
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ 数据库表创建成功！")

if __name__ == "__main__":
    try:
        create_tables()
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        exit(1)  # 确保部署失败时能快速发现