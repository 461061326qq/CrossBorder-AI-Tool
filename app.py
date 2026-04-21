import streamlit as st
import pandas as pd
import time
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

# --- 页面基础配置 ---
st.set_page_config(page_title="AI 智能文案生成器", page_icon="🚀", layout="centered")

# --- 1. 数据库初始化与连接 ---
# Render 会自动注入 DATABASE_URL 环境变量
database_url = os.getenv("DATABASE_URL")

if not database_url:
    st.error("❌ 系统错误：未检测到数据库连接地址 (DATABASE_URL)。请检查 Render 后台设置。")
    st.stop()

# 修复 Render 连接池问题 (重要)
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

try:
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # 连接前检测
        pool_recycle=3600    # 1小时回收连接
    )
except Exception as e:
    st.error(f"❌ 数据库连接失败：{e}")
    st.stop()

# --- 2. 数据库表结构初始化 (如果表不存在则创建) ---
def init_db():
    with engine.begin() as conn:
        # 创建用户表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL,
                balance DECIMAL(10, 2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # 创建生成日志表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS generation_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                product_name VARCHAR(200),
                features TEXT,
                cost DECIMAL(10, 2),
                result_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """))
        # 创建充值记录表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS recharge_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                amount DECIMAL(10, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """))

init_db()

# --- 3. 辅助函数 ---
def get_user_by_username(username):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users WHERE username = :u"), {"u": username})
        return result.mappings().first()

def create_user(username, password):
    try:
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO users (username, password, balance) VALUES (:u, :p, 0)"),
                         {"u": username, "p": password})
        return True
    except SQLAlchemyError:
        return False

def log_generation(user_id, product, features, cost, result):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO generation_logs (user_id, product_name, features, cost, result_text)
            VALUES (:uid, :prod, :feat, :cost, :res)
        """), {"uid": user_id, "prod": product, "feat": features, "cost": cost, "res": result})

def log_recharge(user_id, amount):
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET balance = balance + :amt WHERE id = :uid"),
                     {"amt": amount, "uid": user_id})
        conn.execute(text("INSERT INTO recharge_logs (user_id, amount) VALUES (:uid, :amt)"),
                     {"uid": user_id, "amt": amount})

# --- 4. 会话状态管理 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.balance = 0.0

# --- 5. 侧边栏：登录/注册/充值 ---
with st.sidebar:
    st.title("👤 用户中心")

    if not st.session_state.logged_in:
        menu = ["登录", "注册"]
        choice = st.selectbox("选择操作", menu)

        if choice == "注册":
            st.subheader("创建新账号")
            new_user = st.text_input("用户名", key="reg_user")
            new_pass = st.text_input("密码", type="password", key="reg_pass")
            if st.button("立即注册"):
                if new_user and new_pass:
                    if create_user(new_user, new_pass):
                        st.success("注册成功！请切换到登录页面。")
                    else:
                        st.error("用户名已存在。")
                else:
                    st.warning("请输入用户名和密码。")

        elif choice == "登录":
            st.subheader("用户登录")
            login_user = st.text_input("用户名", key="login_user")
            login_pass = st.text_input("密码", type="password", key="login_pass")
            if st.button("登录"):
                user = get_user_by_username(login_user)
                if user and user['password'] == login_pass:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user['id']
                    st.session_state.username = user['username']
                    st.session_state.balance = float(user['balance'])
                    st.rerun()
                else:
                    st.error("用户名或密码错误。")

    else:
        st.success(f"欢迎, **{st.session_state.username}**")
        st.info(f"💰 当前余额: **¥{st.session_state.balance:.2f}**")

        # 充值功能
        st.markdown("---")
        st.subheader("🔋 充值中心")
        recharge_amt = st.number_input("充值金额", min_value=10, max_value=1000, step=10)
        if st.button("模拟充值"):
            log_recharge(st.session_state.user_id, recharge_amt)
            st.session_state.balance += recharge_amt
            st.success(f"充值成功！当前余额：¥{st.session_state.balance:.2f}")
            st.rerun()

        if st.button("退出登录"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

# --- 6. 主界面逻辑 ---
if not st.session_state.logged_in:
    st.info("👈 请在左侧边栏登录或注册以使用 AI 生成功能")
    st.markdown("""
    ### 欢迎使用 AI 智能文案生成器
    本工具专为电商卖家设计，基于 GPT 模型，能够根据商品特点快速生成高转化率的种草文案。
    """)
else:
    st.title("✨ AI 智能种草文案生成")
    st.markdown("输入商品信息，AI 自动为您撰写吸睛文案。")

    with st.form(key='generate_form'):
        col1, col2 = st.columns(2)
        with col1:
            product_name = st.text_input("商品名称", placeholder="例如：复古蓝牙音箱")
            target_audience = st.selectbox("目标人群", ["大学生", "职场新人", "精致宝妈", "数码极客", "户外爱好者"])

        with col2:
            tone = st.selectbox("文案语气", ["幽默风趣", "专业测评", "情感共鸣", "简单直接", "小红书风"])
            platform = st.selectbox("发布平台", ["小红书", "朋友圈", "抖音脚本", "淘宝详情页"])

        features = st.text_area("商品卖点/特点 (用逗号分隔)", placeholder="例如：音质好，续航长，外观复古，价格便宜")

        submitted = st.form_submit_button("🚀 开始生成 (消耗 ¥0.5)")

        if submitted:
            if not product_name or not features:
                st.warning("请填写商品名称和卖点！")
            elif st.session_state.balance < 0.5:
                st.error("余额不足，请先在左侧充值！")
            else:
                # 模拟 AI 处理过程
                with st.spinner('AI 正在思考中...'):
                    time.sleep(2) # 模拟网络延迟

                    # 这里原本是对接 OpenAI API 的地方，现在为了演示直接生成模拟文案
                    prompt_text = f"{tone}风格的{platform}文案，产品：{product_name}，卖点：{features}"

                    # 模拟生成的文案结果
                    generated_text = f"""
### 🔥 {product_name}：{target_audience}的必备神器！

大家好呀！今天必须给你们按头安利这个我最近挖到的宝藏——**{product_name}**！

💡 **为什么选它？**
- {features.split('，')[0] if '，' in features else features.split(',')[0]}：这点真的太戳我了！
- 另外它的**{features.split('，')[1] if '，' in features and len(features.split('，'))>1 else '设计'}**也非常出色，完全符合我们{target_audience}的审美。

📝 **使用体验**
真的，用过一次就回不去了。特别是当你...（此处省略100字真实体验描述）。

💰 **性价比**
在这个价位能买到这种配置，真的是还要什么自行车？

#好物推荐 #{product_name} #{target_audience}必备
                    """

                # 扣费与记录
                cost = 0.5
                # 更新数据库余额
                with engine.begin() as conn:
                    conn.execute(text("UPDATE users SET balance = balance - :cost WHERE id = :uid"),
                                 {"cost": cost, "uid": st.session_state.user_id})

                # 更新会话状态
                st.session_state.balance -= cost

                # 写入日志
                log_generation(st.session_state.user_id, product_name, features, cost, generated_text)

                st.success("生成成功！已扣除 ¥0.5")
                st.markdown("---")
                st.markdown(generated_text)

    # 历史记录查看
    with st.expander("查看我的生成历史"):
        with engine.connect() as conn:
            df = pd.read_sql_query(
                "SELECT product_name, created_at, cost FROM generation_logs WHERE user_id = :uid ORDER BY created_at DESC",
                conn,
                params={"uid": st.session_state.user_id}
            )
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.write("暂无历史记录")