import os
import psycopg2
from dotenv import load_dotenv

def add_feedback(user_id, action_type, content_id=""):
    # 1. 加载环境变量
    load_dotenv()

    # 2. 获取数据库连接地址
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        print("❌ 错误：未找到 DATABASE_URL，请检查 .env 文件！")
        return

    # 3. 初始化 conn 为 None，确保 finally 能访问到
    conn = None
    cursor = None

    try:
        # 4. 连接数据库
        print("正在连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # 5. 准备 SQL 插入语句
        insert_query = """
        INSERT INTO user_feedback (user_id, action_type, content_id)
        VALUES (%s, %s, %s)
        RETURNING id
        """

        # 6. 执行 SQL
        cursor.execute(insert_query, (user_id, action_type, content_id))

        # 7. 提交事务
        conn.commit()

        # 8. 获取刚插入的 ID
        feedback_id = cursor.fetchone()[0]
        print(f"✅ 成功！数据已写入。记录 ID: {feedback_id}")

    except Exception as error:
        print(f"❌ 发生错误: {error}")

    finally:
        # 9. 关闭连接，释放资源
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
            print("🔒 数据库连接已关闭。")

# --- 主程序入口 ---
if __name__ == "__main__":
    # 模拟一次用户反馈
    # 假设用户 ID 是 'user_123'，类型是 'like'，内容是 '写得真好'
    add_feedback(user_id="user_123", action_type="like", content_id="写得真好")