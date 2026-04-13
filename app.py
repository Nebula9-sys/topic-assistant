import streamlit as st
from openai import OpenAI
from datetime import date
import json
import re
import time

# ─────────────────────────────────────────
# 页面配置
# ─────────────────────────────────────────
st.set_page_config(
    page_title="🔥 爆款选题助手",
    page_icon="🔥",
    layout="wide"
)

# ─────────────────────────────────────────
# 样式
# ─────────────────────────────────────────
st.markdown("""
<style>
.topic-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #e94560;
    border-left: 4px solid #e94560;
    padding: 20px 24px;
    border-radius: 12px;
    margin: 12px 0;
    color: #eee;
}
.topic-title {
    font-size: 18px;
    font-weight: 700;
    color: #ff6b6b;
    margin-bottom: 12px;
}
.topic-tag {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 13px;
    margin-right: 8px;
    font-weight: 600;
}
.tag-score  { background: #ff6b6b22; color: #ff6b6b; border: 1px solid #ff6b6b44; }
.tag-easy   { background: #51cf6622; color: #51cf66; border: 1px solid #51cf6644; }
.tag-medium { background: #ffd43b22; color: #ffd43b; border: 1px solid #ffd43b44; }
.tag-hard   { background: #cc5de822; color: #cc5de8; border: 1px solid #cc5de844; }
.label { color: #888; font-size: 13px; margin-top: 12px; margin-bottom: 4px; }
.value { color: #ddd; font-size: 14px; line-height: 1.7; }
hr { border-color: #333; margin: 24px 0; }

/* 侧边栏样式 */
.mode-card {
    background: #1a1a2e;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
}
.mode-card.active {
    border-color: #e94560;
    background: linear-gradient(135deg, #1a1a2e 0%, #2a1a3e 100%);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 次数限制功能
# ─────────────────────────────────────────
DAILY_LIMIT = 3  # 直接写死在代码里，简单明了

def check_usage_count():
    """检查今日使用次数"""
    today = str(date.today())
    
    if "usage_date" not in st.session_state:
        st.session_state["usage_date"] = today
        st.session_state["usage_count"] = 0
    
    if st.session_state["usage_date"] != today:
        st.session_state["usage_date"] = today
        st.session_state["usage_count"] = 0
    
    return st.session_state["usage_count"]

def add_usage_count():
    """增加使用次数"""
    st.session_state["usage_count"] += 1

def get_remaining():
    """获取剩余次数"""
    used = check_usage_count()
    return max(0, DAILY_LIMIT - used)

# ─────────────────────────────────────────
# 获取预设 API Key（从 Secrets）
# ─────────────────────────────────────────
def get_preset_key():
    """尝试从 Secrets 获取预设 Key"""
    try:
        if hasattr(st, 'secrets') and 'API_KEY' in st.secrets:
            return st.secrets['API_KEY']
    except:
        pass
    return None

# 预设 Key 是否可用
PRESET_KEY_AVAILABLE = get_preset_key() is not None

# ─────────────────────────────────────────
# 侧边栏
# ─────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ 配置")
    st.markdown("---")
    
    # 模式选择
    st.markdown("### 🔑 选择使用模式")
    
    if PRESET_KEY_AVAILABLE:
        # 有预设 Key，显示两种选择
        use_mode = st.radio(
            "使用方式",
            ["🎁 免费体验（每日3次）", "🔑 使用我的 API Key"],
            label_visibility="collapsed"
        )
        
        if "免费" in use_mode:
            # 免费模式
            remaining = get_remaining()
            st.markdown(f"""
            <div style="background:#1a2e1a;padding:12px;border-radius:8px;border:1px solid #51cf66;">
                ✅ <b>免费体验模式</b><br>
                📅 今日剩余：<b style="color:#51cf66;font-size:18px;">{remaining}</b> 次
            </div>
            """, unsafe_allow_html=True)
            api_key_to_use = get_preset_key()
            is_free_mode = True
        else:
            # 自己的 Key
            user_key = st.text_input("你的 API Key", type="password", placeholder="sk-xxxxxxxx")
            api_key_to_use = user_key.strip() if user_key else None
            is_free_mode = False
            
            if api_key_to_use:
                st.markdown("""
                <div style="background:#1a1a2e;padding:12px;border-radius:8px;border:1px solid #e94560;">
                    ✅ <b>自定义 Key 模式</b><br>
                    ♾️ 无使用次数限制
                </div>
                """, unsafe_allow_html=True)
    else:
        # 无预设 Key，只能用自己的
        st.warning("⚠️ 免费额度暂不可用\n请使用你自己的 API Key")
        st.markdown("---")
        user_key = st.text_input("🔑 你的 API Key", type="password", placeholder="sk-xxxxxxxx")
        api_key_to_use = user_key.strip() if user_key else None
        is_free_mode = False
        
        if api_key_to_use:
            st.success("✅ 已配置，可无限使用")
    
    st.markdown("---")
    
    # 生成数量
    topic_count = st.slider("🎯 生成数量", 1, 10, 5)
    
    st.markdown("---")
    
    # 使用说明
    with st.expander("💡 如何获取 API Key"):
        st.markdown("""
        **步骤：**
        
        1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com)
        2. 注册账号
        3. 充值（官网充值，1元可用很久）
        4. 点击「API Keys」→「创建 API Key」
        5. 复制 Key 粘贴到上方输入框
        
        **为什么用 DeepSeek？**
        - 便宜：生成 100 次约 0.3 元
        - 中文质量好
        - 速度快
        """)

# ─────────────────────────────────────────
# 主表单
# ─────────────────────────────────────────
st.title("🔥 爆款选题助手")
st.markdown("输入账号定位，AI 帮你生成高潜力的短视频选题")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    account_niche = st.text_input("📌 账号定位", placeholder="例：职场干货、美食探店、情感治愈")
    target_audience = st.text_input("👥 目标受众", placeholder="例：25-35岁职场女性、大学生")
    platform = st.selectbox("📱 发布平台", ["抖音", "小红书", "视频号", "B站", "快手", "全平台"])

with col2:
    content_style = st.multiselect(
        "🎨 内容风格（可多选）",
        ["干货知识", "搞笑幽默", "情感共鸣", "测评种草", "Vlog记录", "剧情反转", "真实故事", "科普解析", "励志正能量"],
        default=["干货知识"]
    )
    hot_keywords = st.text_input("🌡️ 热点关键词（选填）", placeholder="例：AI副业、情绪价值")
    avoid_topics = st.text_input("🚫 避免方向（选填）", placeholder="例：不想出镜")

st.markdown("---")

# ─────────────────────────────────────────
# Prompt 构建
# ─────────────────────────────────────────
def build_prompt(niche, audience, platform, style, hot, avoid, count):
    return f"""
你是短视频爆款策划专家，擅长分析平台规律、挖掘用户痛点。

## 账号信息
- 定位：{niche}
- 受众：{audience}
- 平台：{platform}
- 风格：{"、".join(style) if style else "不限"}
- 热点：{hot or "暂无"}
- 规避：{avoid or "无"}

## 任务
生成 {count} 个选题，严格返回 JSON 数组，格式：

[
  {{
    "id": 1,
    "title": "视频标题（有冲击力，20字内）",
    "angle": "切入角度（差异化视角）",
    "hook": "前3秒开场话术（直接可用）",
    "outline": "内容大纲（3-4个要点）",
    "score": 85,
    "difficulty": "简单",
    "tip": "针对{platform}的发布建议"
  }}
]

## 要求
- title：纯文本，不用markdown，要能引发好奇或共鸣
- score：60-99 整数，客观评估爆款潜力
- difficulty：只能填「简单」「中等」「较难」
- hook：口语化，能直接当脚本用
"""

# ─────────────────────────────────────────
# 清理文本
# ─────────────────────────────────────────
def clean_text(text):
    if not text:
        return ""
    if isinstance(text, list):
        text = "、".join(str(item) for item in text)
    if not isinstance(text, str):
        text = str(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = text.replace('```', '').replace('`', '')
    return text.strip()

# ─────────────────────────────────────────
# 渲染卡片
# ─────────────────────────────────────────
def render_card(topic):
    diff_map = {"简单": "easy", "中等": "medium", "较难": "hard"}
    diff_cls = diff_map.get(topic.get("difficulty"), "medium")
    score = topic.get("score", 70)
    score_label = f"🔥 {score}分" if score >= 90 else f"⚡ {score}分" if score >= 80 else f"💡 {score}分"

    title = clean_text(topic.get("title", ""))
    angle = clean_text(topic.get("angle", ""))
    hook = clean_text(topic.get("hook", ""))
    outline = clean_text(topic.get("outline", ""))
    tip = clean_text(topic.get("tip", ""))
    diff = topic.get("difficulty", "中等")

    st.markdown(f"""
    <div class="topic-card">
        <div class="topic-title">#{topic['id']} {title}</div>
        <span class="topic-tag tag-score">{score_label}</span>
        <span class="topic-tag tag-{diff_cls}">📹 {diff}</span>
        <div class="label">🎯 核心角度</div>
        <div class="value">{angle}</div>
        <div class="label">🎣 前3秒钩子</div>
        <div class="value">「{hook}」</div>
        <div class="label">📋 内容大纲</div>
        <div class="value">{outline}</div>
        <div class="label">💡 平台建议</div>
        <div class="value">{tip}</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
# 趣味知识（每150字更换一次）
# ─────────────────────────────────────────
fun_facts = [
    "💡 抖音完播率超过 30% 就算优秀",
    "💡 前 3 秒决定 80% 的完播率",
    "💡 标题带数字的点击率提升 15%",
    "💡 晚上 8-10 点是最佳发布时间",
    "💡 情绪共鸣类内容传播力最强",
    "💡 热点话题要 24 小时内跟进",
    "💡 评论区互动率高的视频更容易爆",
    "💡 7-15 秒的视频完播率最高",
    "💡 封面图点击率差异可达 3 倍",
    "💡 第一条评论置顶能提升互动率",
]

# ─────────────────────────────────────────
# 生成按钮
# ─────────────────────────────────────────
if st.button("✨ 开始生成选题", type="primary", use_container_width=True):
    # 检查 API Key
    if not api_key_to_use:
        if PRESET_KEY_AVAILABLE:
            st.error("❌ 出错了，请刷新页面重试")
        else:
            st.error("❌ 请先填入你的 API Key")
        st.stop()
    
    # 检查输入
    if not account_niche.strip():
        st.error("❌ 请填写账号定位")
        st.stop()
    if not target_audience.strip():
        st.error("❌ 请填写目标受众")
        st.stop()
    
    # 检查次数（免费模式）
    if is_free_mode:
        remaining = get_remaining()
        if remaining <= 0:
            st.error("❌ 今日免费次数已用完\n明天再来，或使用你自己的 API Key（无限次数）")
            st.stop()

    # 状态显示
    status_container = st.container()
    
    with status_container:
        status_text = st.empty()
        tip_box = st.empty()
        
        status_text.markdown("### 🤖 AI 正在思考...")
        tip_box.info("💡 生成需要 10-20 秒，请耐心等待")

    try:
        prompt = build_prompt(account_niche, target_audience, platform, content_style, hot_keywords, avoid_topics, topic_count)
        
        client = OpenAI(api_key=api_key_to_use, base_url="https://api.deepseek.com")
        
        # 流式调用
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是爆款选题专家，只返回JSON数组，无其他文字。"},
                {"role": "user", "content": prompt}
            ],
            stream=True,
            temperature=0.85,
            max_tokens=4000
        )
        
        # 接收内容（每150字换提示）
        full_content = ""
        char_count = 0
        tip_index = 0
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                char_count += len(content)
                
                status_text.markdown(f"### ✍️ 正在生成... 已写出 **{char_count}** 字")
                
                # 每 150 字换一个提示
                if char_count // 150 > tip_index:
                    tip_index = char_count // 150
                    tip_box.info(fun_facts[tip_index % len(fun_facts)])
        
        # 解析
        raw = full_content.strip()
        if "```" in raw:
            raw = re.sub(r'```json?\s*', '', raw)
            raw = re.sub(r'```\s*', '', raw)
        
        topics = json.loads(raw.strip())
        
        # 记录使用次数
        if is_free_mode:
            add_usage_count()
        
        # 完成
        status_text.markdown("### ✅ 生成完成！")
        tip_box.success(f"🎉 成功生成 {len(topics)} 个选题")
        time.sleep(0.5)
        status_container.empty()
        
        st.session_state["topics"] = topics
        st.session_state["last_niche"] = account_niche
        st.rerun()
        
    except json.JSONDecodeError:
        status_container.empty()
        st.error("❌ AI 返回格式异常，请重试")
        st.stop()
    except Exception as e:
        status_container.empty()
        st.error(f"❌ 出错了：{e}")
        st.stop()

# ─────────────────────────────────────────
# 展示结果
# ─────────────────────────────────────────
if "topics" in st.session_state:
    topics = st.session_state["topics"]
    niche = st.session_state.get("last_niche", "")

    st.markdown("---")
    st.subheader(f"🎉 为「{niche}」生成了 {len(topics)} 个选题")

    avg = sum(t.get("score", 0) for t in topics) / len(topics)
    high = sum(1 for t in topics if t.get("score", 0) >= 85)

    c1, c2, c3 = st.columns(3)
    c1.metric("📊 平均分", f"{avg:.0f}")
    c2.metric("🔥 高潜力", f"{high} 个")
    c3.metric("📝 总数", f"{len(topics)} 个")

    st.markdown("---")

    sort_opt = st.radio("排序方式", ["按爆款指数", "按难度"], horizontal=True)
    sorted_topics = topics.copy()
    if sort_opt == "按爆款指数":
        sorted_topics.sort(key=lambda x: x.get("score", 0), reverse=True)
    else:
        order = {"简单": 0, "中等": 1, "较难": 2}
        sorted_topics.sort(key=lambda x: order.get(x.get("difficulty", "中等"), 1))

    for t in sorted_topics:
        render_card(t)

    # 导出
    export = f"# {niche} — 爆款选题清单\n\n"
    for t in topics:
        export += f"## {t['id']}. {clean_text(t.get('title',''))}\n"
        export += f"- 爆款指数：{t.get('score')}分 | 拍摄难度：{t.get('difficulty')}\n"
        export += f"- 核心角度：{clean_text(t.get('angle',''))}\n"
        export += f"- 前3秒钩子：{clean_text(t.get('hook',''))}\n"
        export += f"- 内容大纲：{clean_text(t.get('outline',''))}\n"
        export += f"- 平台建议：{clean_text(t.get('tip',''))}\n\n"

    st.markdown("---")
    st.download_button("📥 导出全部选题（TXT）", export, file_name=f"选题_{niche}.txt", use_container_width=True)
