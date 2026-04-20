#!/bin/bash

# 第一步：先运行建表脚本
echo ">>> 正在检查并创建数据库表..."
python src/setup_db.py

# 检查上一步是否成功（可选，但推荐）
if [ $? -ne 0 ]; then
  echo "❌ 建表脚本执行失败，停止启动！"
  exit 1
fi

echo ">>> 数据库准备就绪，正在启动 Streamlit..."

# 第二步：启动 Streamlit（保留你原来的这行命令）
<<<<<<< HEAD
streamlit run app.py --server.port $PORT
=======
streamlit run app.py --server.port $PORT
>>>>>>> 514cbac7fa253461aec466643af09e23bc46431c
