import os
import psycopg2
from dotenv import load_dotenv

def main():
    # 1. 加载环境变量
    load_dotenv()

    # 2. 获取数据库地址
    db_url = os.environ.get("DATABASE_URL")

    # 3. 检查地址是否存在
    if not db_url:
        print("❌ 错误：没有找到数据库连接地址 (DATABASE_URL)！")
        return

    print("🔗 正在连接云端数据库...")

    try:
        # 4. 建立连接
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # 5. 创建“用户表”
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(200) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 6. 创建“反馈表”
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(200) NOT NULL,
                platform VARCHAR(50),
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 提交更改
        conn.commit()
        print("✅ 数据库表检查/创建成功！")

    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
    finally:
        # 关闭连接
        if 'conn' in locals():
            cur.close()
            conn.close()

# ⚠️ 关键：必须在这里调用 main 函数，代码才会运行！
if __name__ == "__main__":
    main()