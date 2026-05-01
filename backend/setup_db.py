import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def main():
    # 1. 加载环境变量
    load_dotenv()

    # 2. 获取数据库地址
    db_url = os.environ.get("DATABASE_URL")

    # 3. 检查地址是否存在
    if not db_url:
        print("❌ 错误: 没有找到数据库连接地址 (DATABASE_URL)")
        return

    # 4. 兼容 Render/Heroku 的 postgres:// 协议前缀问题
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print("🚀 正在连接云端数据库...")

    try:
        # 5. 使用 SQLAlchemy 建立连接 (自动处理 URL 解析)
        engine = create_engine(db_url)

        with engine.begin() as conn: # begin() 会自动 commit 或 rollback
            # 6. 创建“用户表” (必须包含 app.py 需要的字段)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    "username" VARCHAR(200) UNIQUE NOT NULL,
                    password_hash VARCHAR(200) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ 'users' 表检查/创建成功")

            # 7. 创建“反馈表”
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    user_email VARCHAR(200) NOT NULL,
                    platform VARCHAR(50),
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ 'feedback' 表检查/创建成功")

        print("🎉 数据库初始化完成！")

    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")

if __name__ == "__main__":
    main()