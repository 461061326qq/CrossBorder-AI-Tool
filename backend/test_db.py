import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 1. 读取刚才的 .env 文件
load_dotenv()

# 2. 获取连接地址
db_url = os.getenv("DATABASE_URL")

if not db_url:
    print("❌ 错误：没有找到 DATABASE_URL，请检查 .env 文件")
else:
    print("🔗 正在尝试连接云端数据库...")
    try:
        # 3. 创建引擎
        engine = create_engine(db_url)
        
        # 4. 尝试连接并执行一个简单命令
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"✅ 穿针成功！数据库已连接，测试返回值: {result.fetchone()}")
            
    except Exception as e:
        print("❌ 穿针失败！报错信息如下：")
        print(e)