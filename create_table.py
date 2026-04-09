import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 1. 加载环境变量
load_dotenv()

# 2. 获取数据库连接地址
db_url = os.getenv("DATABASE_URL")

if not db_url:
    print("❌ 错误：没有找到 DATABASE_URL，请检查 .env 文件")
else:
    print("🚀 正在尝试连接云端数据库以创建数据表...")
    
    try:
        # 3. 创建引擎
        engine = create_engine(db_url)
        
        # 4. 定义建表 SQL (这是作战地图里的“埋雷”步骤)
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS user_feedback (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50),       -- 用户ID (暂时可用 session_id)
            content_id VARCHAR(50),    -- 关联生成的文案ID
            action_type VARCHAR(10),   -- 动作类型: 'like' 或 'dislike'
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # 5. 执行建表
        with engine.connect() as connection:
            connection.execute(text(create_table_sql))
            connection.commit() # 提交事务
            
        print("✅ 成功！数据表 'user_feedback' 已创建或已存在。")
        print("💡 现在可以去写点赞功能的代码了！")

    except Exception as e:
        print("❌ 建表失败！报错信息如下：")
        print(e)