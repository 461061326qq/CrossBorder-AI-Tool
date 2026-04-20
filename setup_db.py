import os
import psycopg2
from dotenv import load_dotenv
def main():
      load_dotenv()
    # 1. 从 Render 的环境变量里自动获取数据库地址
    db_url = os.environ.get("DATABASE_URL")
    
    if not db_url:
        print("❌ 错误：没有找到数据库连接地址！")
        return

    print("🔗 正在连接云端数据库...")
    
    try:
        # 2. 建立连接
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # 3. 创建“用户表”
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(200) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. 创建“反馈表”
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(200) NOT NULL,
                platform VARCHAR(50), 
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 5. 保存并关闭
        conn.commit()
        cur.close()
        conn.close()
        
        print("🎉 成功！数据库表已创建/更新。")
        print("✅ 表1: users (用户信息)")
        print("✅ 表2: feedback (用户反馈与生成记录)")

    except Exception as e:
        print(f"❌ 出错了: {e}")

if __name__ == "__main__":
    main()