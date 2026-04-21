import os
import time
import logging
import streamlit as st
import json
import pandas as pd
from sqlalchemy import create_engine, text
from passlib.context import CryptContext
from datetime import datetime
# 新增：导入 OpenAI SDK
from openai import OpenAI

# ==========================================
# 1. 基础配置与日志
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('SEOApp')

# ==========================================
# 2. 数据库与安全配置
# ==========================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 数据库连接
def get_db_engine():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL 环境变量未设置")
        return None
    
    # 修复 Postgres 协议前缀
    if db_url.startswith('postgres://'):
        db_url = 'postgresql://' + db_url[len('postgres://'):]
    
    try:
        engine = create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )
        return engine
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None

# 初始化数据库表
def init_db():
    engine = get_db_engine()
    if not engine:
        return False
    try:
        with engine.begin() as conn:
            # 创建用户表
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # 创建余额表
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS balances (
                    user_id INTEGER PRIMARY KEY,
                    balance DECIMAL(10, 2) DEFAULT 100.00,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """))
            # 创建历史记录表
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    topic VARCHAR(255),
                    platform VARCHAR(50),
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """))
            logger.info("数据库初始化成功")
            return True
    except Exception as e:
        logger.error(f"数据库建表失败: {e}")
        return False

# ==========================================
# 3. 多语言加载系统
# ==========================================
@st.cache_data
def load_translations():
    """加载多语言文件，如果不存在则返回默认结构"""
    languages = {}
    lang_dir = 'languages'
    # 默认英文回退
    default_translations = {
        "login_title": "SEO Content Generator",
        "username": "Username",
        "password": "Password",
        "login_btn": "Login",
        "register_btn": "Register",
        "logout": "Logout",
        "topic_input": "Enter Topic",
        "platform_select": "Select Platform",
        "generate_btn": "Generate Content",
        "history_title": "Generation History",
        "balance": "Balance",
        "error_empty_topic": "Please enter a topic",
        "error_low_balance": "Insufficient balance",
        "success_generation": "Content generated successfully",
        "register_success": "Registration successful, please login"
    }
    languages['en'] = default_translations
    
    # 尝试加载中文
    try:
        if os.path.exists(f'{lang_dir}/zh.json'):
            with open(f'{lang_dir}/zh.json', 'r', encoding='utf-8') as f:
                languages['zh'] = json.load(f)
        else:
            # 如果文件不存在，创建一个默认的
            os.makedirs(lang_dir, exist_ok=True)
            with open(f'{lang_dir}/zh.json', 'w', encoding='utf-8') as f:
                json.dump({
                    "login_title": "SEO 内容生成器",
                    "username": "用户名",
                    "password": "密码",
                    "login_btn": "登录",
                    "register_btn": "注册",
                    "logout": "退出登录",
                    "topic_input": "输入主题",
                    "platform_select": "选择平台",
                    "generate_btn": "生成内容",
                    "history_title": "生成历史",
                    "balance": "余额",
                    "error_empty_topic": "请输入主题",
                    "error_low_balance": "余额不足",
                    "success_generation": "内容生成成功",
                    "register_success": "注册成功，请登录"
                }, f, ensure_ascii=False, indent=4)
            languages['zh'] = json.load(open(f'{lang_dir}/zh.json', 'r', encoding='utf-8'))
    except Exception as e:
        logger.error(f"加载语言包失败: {e}")
        languages['zh'] = default_translations
    return languages

def get_text(lang_code, key):
    translations = load_translations()
    lang_dict = translations.get(lang_code, translations['en'])
    return lang_dict.get(key, key)

# ==========================================
# 4. 核心业务逻辑类 (已修复 AI 生成部分)
# ==========================================
class SEOGenerator:
    def __init__(self, user_id, engine):
        self.user_id = user_id
        self.engine = engine
        # 初始化 OpenAI 客户端 (兼容 DeepSeek/百炼)
        # 确保 .env 中配置了 BASE_URL 和 API_KEY
        api_key = os.getenv("API_KEY")
        base_url = os.getenv("BASE_URL", "https://api.openai.com/v1") # 默认 OpenAI
        
        if not api_key:
            logger.error("API_KEY 未设置")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            logger.info(f"AI 客户端初始化成功: {base_url}")

    def get_balance(self):
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT balance FROM balances WHERE user_id = :uid"), {"uid": self.user_id})
            row = result.fetchone()
            return float(row[0]) if row else 0.0

    def deduct_balance(self, amount):
        with self.engine.begin() as conn:
            conn.execute(text("UPDATE balances SET balance = balance - :amt WHERE user_id = :uid"), {"amt": amount, "uid": self.user_id})

    def save_history(self, topic, platform, content):
        with self.engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO history (user_id, topic, platform, content) 
                VALUES (:uid, :topic, :platform, :content)
            """), {"uid": self.user_id, "topic": topic, "platform": platform, "content": content})

    def generate_content(self, platform, topic, lang):
        # 构建提示词
        prompts = {
            'blog': f"Write a professional SEO blog post about '{topic}'. Use markdown format.",
            'instagram': f"Write a catchy Instagram caption about '{topic}'. Include emojis and hashtags.",
            'linkedin': f"Write a professional LinkedIn post about '{topic}'. Focus on industry insights."
        }
        system_prompt = "You are an expert SEO content creator."
        user_prompt = prompts.get(platform, f"Write content about {topic}")

        if not self.client:
            return "Error: API Key not configured."

        try:
            # 调用 AI 模型 (自动适配 DeepSeek/百炼)
            response = self.client.chat.completions.create(
                model=os.getenv("MODEL_NAME", "gpt-3.5-turbo"), # 默认模型
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI 生成失败: {e}")
            return f"Error generating content: {str(e)}"

# ==========================================
# 5. 页面渲染逻辑
# ==========================================
def show_login():
    st.session_state['page'] = 'login'

def show_dashboard():
    if 'user_id' not in st.session_state:
        show_login()
        return
    
    engine = st.session_state['engine']
    lang = st.session_state.get('language', 'en')
    generator = SEOGenerator(st.session_state['user_id'], engine)

    st.sidebar.title(get_text(lang, "login_title"))
    st.sidebar.write(f"👤 {st.session_state['username']}")
    st.sidebar.write(f"💰 {get_text(lang, 'balance')}: ${generator.get_balance():.2f}")
    
    if st.sidebar.button(get_text(lang, "logout")):
        for key in ['user_id', 'username', 'page']:
            st.session_state.pop(key, None)
        st.rerun()

    st.header(get_text(lang, "generate_btn"))
    
    # 输入区域
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input(get_text(lang, "topic_input"))
    with col2:
        platform = st.selectbox(get_text(lang, "platform_select"), ['blog', 'instagram', 'linkedin'])

    if st.button(get_text(lang, "generate_btn")):
        if not topic:
            st.warning(get_text(lang, "error_empty_topic"))
        elif generator.get_balance() < 5.0:
            st.error(get_text(lang, "error_low_balance"))
        else:
            with st.spinner("Generating..."):
                content = generator.generate_content(platform, topic, lang)
                if content.startswith("Error"):
                    st.error(content)
                else:
                    st.success(get_text(lang, "success_generation"))
                    st.markdown(f"---\n{content}\n---")
                    # 保存数据
                    generator.deduct_balance(5.0)
                    generator.save_history(topic, platform, content)
                    st.rerun()

    # 历史记录
    st.subheader(get_text(lang, "history_title"))
    with engine.connect() as conn:
        df = pd.read_sql_query(
            "SELECT topic, platform, created_at FROM history WHERE user_id = :uid ORDER BY created_at DESC LIMIT 10",
            conn, params={"uid": st.session_state['user_id']}
        )
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No history yet.")

# ==========================================
# 6. 主程序入口
# ==========================================
def main():
    # 1. 环境变量检查
    if not os.getenv('DATABASE_URL'):
        st.error("❌ Critical Error: DATABASE_URL environment variable is not set.")
        st.stop()
    
    # 2. 数据库初始化
    engine = get_db_engine()
    if not engine:
        st.error("❌ Failed to connect to database.")
        st.stop()
    if not init_db():
        st.error("❌ Database initialization failed.")
        st.stop()

    # 3. 全局状态初始化
    if 'engine' not in st.session_state:
        st.session_state['engine'] = engine
    if 'page' not in st.session_state:
        st.session_state['page'] = 'login'
    if 'language' not in st.session_state:
        st.session_state['language'] = 'en'

    # 4. 页面路由
    if st.session_state['page'] == 'login':
        # 登录界面
        st.title("🚀 SEO Content Generator")
        lang = st.selectbox("Language", ['en', 'zh'], index=0)
        st.session_state['language'] = lang
        
        tab1, tab2 = st.tabs([get_text(lang, "login_btn"), get_text(lang, "register_btn")])
        
        with tab1:
            username = st.text_input(get_text(lang, "username"), key="login_user")
            password = st.text_input(get_text(lang, "password"), type="password", key="login_pass")
            if st.button(get_text(lang, "login_btn")):
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT id, password_hash FROM users WHERE username = :user"), {"user": username})
                    row = result.fetchone()
                    if row and pwd_context.verify(password, row[1]):
                        st.session_state['user_id'] = row[0]
                        st.session_state['username'] = username
                        st.session_state['page'] = 'dashboard'
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        
        with tab2:
            new_user = st.text_input(get_text(lang, "username"), key="reg_user")
            new_pass = st.text_input(get_text(lang, "password"), type="password", key="reg_pass")
            if st.button(get_text(lang, "register_btn")):
                try:
                    hashed = pwd_context.hash(new_pass)
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO users (username, password_hash) VALUES (:user, :hash)"), {"user": new_user, "hash": hashed})
                        # 初始化余额
                        user_res = conn.execute(text("SELECT id FROM users WHERE username = :user"), {"user": new_user})
                        uid = user_res.fetchone()[0]
                        conn.execute(text("INSERT INTO balances (user_id) VALUES (:uid)"), {"uid": uid})
                    st.success(get_text(lang, "register_success"))
                except Exception as e:
                    st.error("Username already exists")
                    
    elif st.session_state['page'] == 'dashboard':
        show_dashboard()

if __name__ == "__main__":
    main()