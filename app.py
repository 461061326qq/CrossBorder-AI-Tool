import streamlit as st
import time
import random
import pandas as pd
import base64

# --- 页面配置 ---
st.set_page_config(
    page_title="CrossBorder AI Copywriter Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 初始化 Session State (统一管理) ---
if 'generated_copy' not in st.session_state:
    st.session_state.generated_copy = ""
if 'show_results' not in st.session_state:
    st.session_state.show_results = False
if 'token_count' not in st.session_state:
    st.session_state.token_count = 0
if 'save_voice' not in st.session_state:
    st.session_state.save_voice = False
if 'user_subscription' not in st.session_state:
    st.session_state.user_subscription = "free"
# --- 自定义 CSS 样式 (1:1 还原截图) ---
st.markdown("""
    <style>
    /* 全局字体与背景 */
    body { font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; background-color: #f4f6f8; }
    .stApp { background-color: #ffffff; padding: 20px; border-radius: 10px; }
    
    /* 隐藏默认菜单 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 侧边栏样式重构 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
        padding: 20px;
        width: 300px !important;
    }
    
    /* 侧边栏头像 */
    .sidebar-avatar { text-align: center; margin-bottom: 20px; }
    .sidebar-avatar img { width: 80px; height: 80px; border-radius: 50%; border: 3px solid #00C48C; }
    .sidebar-title { font-size: 18px; font-weight: bold; color: #333; margin-top: 10px; }
    
    /* 成本优势块 */
    .cost-box { background-color: #f0f9eb; padding: 15px; border-radius: 8px; border: 1px solid #e1f3d8; margin-bottom: 20px; }
    .cost-title { color: #67c23a; font-weight: bold; font-size: 14px; margin-bottom: 10px; display: flex; align-items: center; }
    .cost-title::before { content: '💰'; margin-right: 5px; }
    .cost-item { font-size: 12px; color: #666; margin-bottom: 5px; }
    .cost-highlight { color: #f56c6c; font-weight: bold; background: #fef0f0; padding: 2px 5px; border-radius: 4px; }
    
    /* 使用量列表 */
    .usage-title { color: #409eff; font-weight: bold; font-size: 14px; margin-bottom: 10px; display: flex; align-items: center; }
    .usage-title::before { content: '📊'; margin-right: 5px; }
    .usage-list { list-style: none; padding-left: 0; font-size: 12px; color: #666; }
    .usage-list li { margin-bottom: 8px; display: flex; justify-content: space-between; }
    
    /* 底部 */
    .sidebar-footer { margin-top: 50px; font-size: 11px; color: #999; text-align: center; border-top: 1px solid #eee; padding-top: 10px; }

    /* 主界面头部 */
    .main-header { font-size: 28px; font-weight: 800; color: #1f2329; margin-bottom: 25px; }
    
    /* 结果页看板 */
    .metrics-container { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 25px; }
    .metric-card { background: linear-gradient(135deg, #00C48C 0%, #00996e 100%); color: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 4px 6px rgba(0, 196, 140, 0.2); }
    .metric-val { font-size: 20px; font-weight: bold; margin-top: 5px; }
    .metric-label { font-size: 12px; opacity: 0.9; }
    
    /* 成本统计行 */
    .cost-stats { display: flex; justify-content: space-between; background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 20px; font-size: 13px; color: #555; }
    .cost-item-stat { display: flex; align-items: center; }
    .cost-item-stat span { margin-left: 5px; font-weight: bold; color: #333; }
    
    /* 按钮样式 */
    .stButton>button {
        background-color: #00C48C; color: white; font-weight: bold; border: none; border-radius: 6px; height: 45px; width: 100%;
        transition: all 0.3s; box-shadow: 0 4px 6px rgba(0, 196, 140, 0.2);
    }
    .stButton>button:hover { background-color: #00a376; transform: translateY(-1px); }
    
    /* 满意度 */
    .satisfaction { margin-top: 20px; font-size: 14px; font-weight: bold; color: #333; }
    </style>
""", unsafe_allow_html=True)

# --- 侧边栏重构 ---
with st.sidebar:
    # 头像区
    st.markdown("""
    <div class="sidebar-avatar">
        <img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" alt="Avatar">
        <div class="sidebar-title">CrossBorder AI<br>Copywriter Pro</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 成本优势
    st.markdown("""
    <div class="cost-box">
        <div class="cost-title">成本优势</div>
        <div class="cost-item">我们的成本: <strong>¥8.00</strong>/百万 tokens</div>
        <div class="cost-item">Jasper成本: <strong>¥120.00</strong>/百万 tokens</div>
        <div class="cost-item">成本优势: <span class="cost-highlight">93% 更低</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    # 使用量
    st.markdown("""
    <div class="usage-section">
        <div class="usage-title">您的使用量</div>
        <ul class="usage-list">
            <li><span>当前计划:</span> <span style="color:#00C48C; font-weight:bold;">FREE 免费</span></li>
            <li><span>已用文案:</span> <span>0/5</span></li>
            <li><span>累计节省:</span> <span>$0.00</span></li>
            <li><span>翻译为:</span> <span>...</span></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 底部
    st.markdown('<div class="sidebar-footer">AI服务: DeepSeek + 阿里云</div>', unsafe_allow_html=True)

# --- 主界面逻辑 ---
# Tab 切换
tab1, tab2 = st.tabs(["📝 生成文案", "🔍 竞品分析"])

# --- Tab 1: 生成文案 ---
with tab1:
    if not st.session_state.show_results:
        # --- 输入表单 ---
        st.markdown('<div class="main-header">AI 跨境电商文案专家</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1]) # 左侧宽，右侧窄
        
        with col1:
            product_name = st.text_input("产品名称", value="Toy Storage Box")
            product_features = st.text_area("产品特点", value="透明塑料收纳盒, 防尘防潮, 玩具整理, 可堆叠收纳箱", height=100)
            target_platform = st.selectbox("目标平台", ["Amazon", "Shopify", "TikTok Shop", "eBay"], index=0)
            
        with col2:
            brand_tone = st.selectbox("品牌调性", ["专业", "幽默", "亲切", "高端"])
            output_lang = st.selectbox("输出语言", ["英语 (English)", "中文", "日语", "德语"])
            keywords = st.text_input("核心关键词", value="toy organizer, kids storage")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 生成按钮
        if st.button("🚀 一键生成爆款文案"):
            with st.spinner("AI正在深度分析关键词与竞品..."):
                time.sleep(2) # 模拟思考时间
                
                # 模拟生成结果
                st.session_state.generated_copy = f"""
**Title:** Premium Transparent Stackable Toy Storage Box - Dustproof & Moisture-Proof Organizer for Kids Room

**Bullet Points:**
- ✅ **Crystal Clear Visibility:** Easily identify toys without opening the box.
- ✅ **Stackable Design:** Maximize vertical space in any room.
- ✅ **Durable Material:** Made from high-quality, non-toxic plastic.
- ✅ **Versatile Use:** Perfect for LEGOs, dolls, and art supplies.

**Description:**
Keep your home clutter-free with our ultimate {product_name}. Designed for modern parents...
                """
                st.session_state.token_count = random.randint(400, 600)
                st.session_state.show_results = True
                st.rerun()

    else:
        # --- 结果展示页 ---
        st.markdown('<div class="main-header">生成结果预览</div>', unsafe_allow_html=True)
        
        # 1. 预计效果看板 (4个卡片)
        st.markdown("""
        <div class="metrics-container">
            <div class="metric-card"><div class="metric-label">CTR 点击率提升</div><div class="metric-val">+22.5%</div></div>
            <div class="metric-card"><div class="metric-label">预计 CTR 转化率</div><div class="metric-val">5.6%</div></div>
            <div class="metric-card"><div class="metric-label">月省广告费</div><div class="metric-val">$124.5</div></div>
            <div class="metric-card"><div class="metric-label">ROI 投资回报</div><div class="metric-val">1:4.8</div></div>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. 文案内容展示
        st.text_area("AI 生成文案", value=st.session_state.generated_copy, height=300)
        
        # 3. 操作按钮行
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        with col_btn1:
            if st.button("📋 复制文案"):
                st.success("已复制到剪贴板")
        with col_btn2:
            # 下载功能实现
            def convert_df(df):
                return df.to_csv().encode('utf-8')
            csv = convert_df(pd.DataFrame([{"Copy": st.session_state.generated_copy}]))
            st.download_button(label="📥 下载文案", data=csv, file_name='copywriting.csv', mime='text/csv')
            
        with col_btn3:
            # 保存到品牌声音
            save_voice = st.checkbox("✅ 保存到品牌声音", value=st.session_state.save_voice)
            st.session_state.save_voice = save_voice

        # 4. 成本统计条
        cost_self = st.session_state.token_count * 0.000008 # 8元/百万
        cost_jasper = st.session_state.token_count * 0.00012 # 120元/百万
        
        st.markdown(f"""
        <div class="cost-stats">
            <div class="cost-item-stat">Token 消耗: <span>{st.session_state.token_count}</span></div>
            <div class="cost-item-stat">本次成本: <span>¥{cost_self:.5f}</span></div>
            <div class="cost-item-stat" style="color:#999">Jasper等效成本: <span style="text-decoration:line-through">¥{cost_jasper:.5f}</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        # 5. 满意度评分
        st.markdown('<div class="satisfaction">😃 您对结果满意吗？</div>', unsafe_allow_html=True)
           # --- 替换为简易反馈按钮 ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 有帮助"):
            st.success("感谢反馈！")
    with col2:
        if st.button("👎 需改进"):
            st.info("收到，我们会优化！")
        
        # 返回按钮
        if st.button("↩️ 返回修改"):
            st.session_state.show_results = False
            st.rerun()

# --- Tab 2: 竞品分析 ---
with tab2:
    st.markdown('<div class="main-header">🔍 竞品深度分析</div>', unsafe_allow_html=True)
    
    asin_input = st.text_input("输入竞品 ASIN (支持批量，逗号分隔)", placeholder="例如: B08XYZ1234, B09ABC5678")
    
    if st.button("开始分析竞品"):
        if asin_input:
            with st.spinner("正在抓取竞品数据..."):
                time.sleep(2)
                st.success("分析完成！")
                # 模拟数据表格
                data = {
                    'ASIN': [asin.strip() for asin in asin_input.split(',')],
                    '月销量': [random.randint(500, 2000) for _ in range(len(asin_input.split(',')))],
                    '均价': [random.randint(15, 40) for _ in range(len(asin_input.split(',')))],
                    '核心卖点': ['大容量设计', '环保材质'] * (len(asin_input.split(','))//2 + 1),
                    '差评痛点': ['盖子容易坏', '塑料味重'] * (len(asin_input.split(','))//2 + 1)
                }
                st.dataframe(pd.DataFrame(data), use_container_width=True)
                st.info("💡 建议：针对竞品的“盖子容易坏”痛点，可以在文案中强调我们产品的“加固卡扣设计”。")
        else:
            st.warning("请输入至少一个 ASIN")

# --- 底部版权 ---
st.markdown("<br><br><hr><div style='text-align: center; color: #999; font-size: 12px;'>© 2024 CrossBorder AI Inc. | 隐私政策 | 服务条款</div>", unsafe_allow_html=True)