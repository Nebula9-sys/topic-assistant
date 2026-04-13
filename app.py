import streamlit as st
from openai import OpenAI
import json
import re
import time
import random

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
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 侧边栏
# ─────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ 配置")
    st.markdown("---")
    api_key = st.text_input("🔑 API Key", type="password", placeholder="sk-xxxxxxxx")
    api_provider = st.radio("API 提供商", ["DeepSeek（推荐）", "OpenAI"], index=0)
    model_options = {
        "DeepSeek（推荐）": {"base_url": "https://api.deepseek.com", "model": "deepseek-chat"},
        "OpenAI": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"}
    }
    selected = model_options[api_provider]
    st.markdown("---")
    topic_count = st.slider("🎯 生成数量", 5, 15, 10, 5)

# ─────────────────────────────────────────
# 主表单
# ─────────────────────────────────────────
st.title("🔥 爆款选题助手")
st.markdown("输入账号定位，AI 生成高潜力选题")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    account_niche = st.text_input("📌 账号定位", placeholder="例：职场干货、美食探店")
    target_audience = st.text_input("👥 目标受众", placeholder="例：25-35岁职场人")
    platform = st.selectbox("📱 平台", ["抖音", "小红书", "视频号", "B站", "快手", "全平台"])

with col2:
    content_style = st.multiselect(
        "🎨 内容风格",
        ["干货知识", "搞笑幽默", "情感共鸣", "测评种草", "Vlog记录", "剧情反转", "真实故事", "科普解析", "励志正能量"],
        default=["干货知识"]
    )
    hot_keywords = st.text_input("🌡️ 热点关键词（选填）", placeholder="例：AI副业")
    avoid_topics = st.text_input("🚫 避免方向（选填）", placeholder="例：不出镜")

st.markdown("---")

# ─────────────────────────────────────────
# Prompt 构建
# ─────────────────────────────────────────
def build_prompt(niche, audience, platform, style, hot, avoid, count):
    return f"""
你是短视频爆款策划专家。

账号定位：{niche}
目标受众：{audience}
平台：{platform}
风格：{"、".join(style) if style else "不限"}
热点：{hot or "无"}
规避：{avoid or "无"}

生成 {count} 个选题，严格返回 JSON 数组：

[
  {{
    "id": 1,
    "title": "视频标题",
    "angle": "切入角度",
    "hook": "前3秒开场话术",
    "outline": "内容大纲",
    "score": 85,
    "difficulty": "简单",
    "tip": "平台建议"
  }}
]

要求：
- title 纯文本，不用markdown格式
- score 是60-99整数
- difficulty 只能是：简单/中等/较难
- outline 和 hook 用字符串，不要用数组
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
# AI 调用
# ─────────────────────────────────────────
def generate_topics(api_key, base_url, model, prompt):
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是爆款选题专家，只返回JSON数组。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.85,
        max_tokens=4000
    )
    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        raw = re.sub(r'```json?\s*', '', raw)
        raw = re.sub(r'```\s*', '', raw)
    return json.loads(raw.strip())

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
# 趣味提示语
# ─────────────────────────────────────────
fun_tips = [
    "🔍 正在分析同类账号爆款规律...",
    "📊 正在计算选题爆款指数...",
    "🎯 正在匹配目标用户痛点...",
    "✂️ 正在优化前3秒钩子话术...",
    "🧠 AI 正在头脑风暴中...",
    "💡 正在提炼核心创意角度...",
]

fun_facts = [
    "💡 抖音完播率超过 30% 就算优秀",
    "💡 前 3 秒决定 80% 的完播率",
    "💡 标题带数字的点击率提升 15%",
    "💡 晚上 8-10 点是最佳发布时间",
    "💡 情绪共鸣类内容传播力最强",
    "💡 热点话题要 24 小时内跟进",
]

# ─────────────────────────────────────────
# 生成按钮
# ─────────────────────────────────────────
if st.button("✨ 开始生成", type="primary", use_container_width=True):
    if not api_key:
        st.error("❌ 请填入 API Key")
        st.stop()
    if not account_niche:
        st.error("❌ 请填写账号定位")
        st.stop()
    if not target_audience:
        st.error("❌ 请填写目标受众")
        st.stop()

    progress_bar = st.progress(0)
    status_text = st.empty()
    tip_box = st.empty()

    for i in range(4):
        progress_bar.progress((i + 1) * 25)
        status_text.markdown(f"### {fun_tips[i % len(fun_tips)]}")
        tip_box.info(fun_facts[i % len(fun_facts)])
        time.sleep(0.5)

    status_text.markdown("### 🤖 AI 正在生成选题...")
    tip_box.empty()

    try:
        prompt = build_prompt(account_niche, target_audience, platform, content_style, hot_keywords, avoid_topics, topic_count)
        topics = generate_topics(api_key, selected["base_url"], selected["model"], prompt)
        
        progress_bar.progress(100)
        status_text.markdown("### ✅ 生成完成！")
        time.sleep(0.3)
        
        progress_bar.empty()
        status_text.empty()
        
        st.session_state["topics"] = topics
        st.session_state["last_niche"] = account_niche
        
    except json.JSONDecodeError:
        progress_bar.empty()
        status_text.empty()
        st.error("❌ AI 返回格式错误，请重试")
        st.stop()
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
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

    sort_opt = st.radio("排序", ["按爆款指数", "按难度"], horizontal=True)
    sorted_topics = topics.copy()
    if sort_opt == "按爆款指数":
        sorted_topics.sort(key=lambda x: x.get("score", 0), reverse=True)
    else:
        order = {"简单": 0, "中等": 1, "较难": 2}
        sorted_topics.sort(key=lambda x: order.get(x.get("difficulty", "中等"), 1))

    for t in sorted_topics:
        render_card(t)

    export = f"# {niche} 选题清单\n\n"
    for t in topics:
        export += f"## {t['id']}. {clean_text(t.get('title',''))}\n"
        export += f"- 指数：{t.get('score')}分 | 难度：{t.get('difficulty')}\n"
        export += f"- 角度：{clean_text(t.get('angle',''))}\n"
        export += f"- 钩子：{clean_text(t.get('hook',''))}\n"
        export += f"- 大纲：{clean_text(t.get('outline',''))}\n\n"

    st.markdown("---")
    st.download_button("📥 导出 TXT", export, file_name=f"选题_{niche}.txt", use_container_width=True)
