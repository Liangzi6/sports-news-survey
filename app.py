# ============================================================
# 📘 体育新闻感知研究问卷系统（最终科研版）
# ============================================================

import streamlit as st
import pandas as pd
import datetime, os, uuid, requests, zipfile, random

# ✅ Google Apps Script Web App 地址
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzFJpJGK_pMcbRNzNFgLCl-dTLusdEXF_n03ElTiSpX7iCqebLtWFvPHPpcu4mPKxAyyQ/exec"

# ✅ Streamlit 页面设置
st.set_page_config(page_title="体育新闻感知研究问卷", layout="wide")

# ============================================================
# 🗂️ 自动解压与文件检查
# ============================================================
if os.path.exists("generated_questionnaires.zip") and not os.path.exists("generated_questionnaires"):
    with zipfile.ZipFile("generated_questionnaires.zip", "r") as zip_ref:
        zip_ref.extractall("generated_questionnaires")

QUESTION_DIR = "./generated_questionnaires"
if not os.path.exists(QUESTION_DIR) or not os.listdir(QUESTION_DIR):
    st.error("❌ 未检测到问卷文件，请检查 generated_questionnaires 文件夹。")
    st.stop()

files = sorted([f for f in os.listdir(QUESTION_DIR) if f.endswith(".xlsx")])

if "chosen_file" not in st.session_state:
    st.session_state.chosen_file = random.choice(files)

chosen_file = st.session_state.chosen_file
file_path = os.path.join(QUESTION_DIR, chosen_file)
df_questions = pd.read_excel(file_path)
qid = os.path.splitext(chosen_file)[0].replace("questionnaire_", "")

# ============================================================
# 🏁 页面内容
# ============================================================
st.title("🏟️ 体育新闻感知研究问卷")

st.info("""
📌 **研究声明 / Research Statement**
本研究旨在探究读者对体育新闻真实性的感知及其影响因素。问卷匿名，数据仅用于学术研究。
某些标题可能包含虚构或改写成分。继续填写即表示您同意参与。
""")

agree = st.checkbox("我已阅读并同意参与本研究 / I agree to participate")
if not agree:
    st.stop()

# ============================================================
# 👤 第一部分：基本信息 (含体育知识水平)
# ============================================================
st.header("一、基本信息")
col1, col2 = st.columns(2)
with col1:
    age = st.radio("1️⃣ 您的年龄？", ["18-25岁", "26-35岁", "36-45岁", "46岁以上"])
    edu = st.radio("2️⃣ 您的教育程度？", ["高中及以下", "大专", "本科", "硕士及以上"])
with col2:
    freq = st.radio("3️⃣ 您每周阅读体育新闻的频率？", ["<1次", "1-3次", "4-7次", ">7次"])
    # [新增] 体育知识水平
    sports_knowledge = st.select_slider(
        "4️⃣ 您认为自己对体育赛事和相关新闻的了解程度？",
        options=["完全不了解", "略有了解", "一般", "比较了解", "非常了解"],
        value="一般"
    )

if freq == "<1次":
    st.warning("感谢参与！由于您平时较少阅读体育新闻，本调查暂不需要您的数据。")
    st.stop()

# ============================================================
# 🤖 第二部分：AI Familiarity (优化频率选项)
# ============================================================
st.header("二、AI 熟悉度")
# [修改] 使用更精确的频率
ai_use = st.radio("5️⃣ 您使用 ChatGPT 或类似生成式 AI 工具的频率？", 
                 ["从不使用", "每月1-2次", "每周1-2次", "每周3次以上", "几乎每天"])
ai_know = st.select_slider("6️⃣ 您对“生成式 AI”生成文本内容的原理了解程度？", 
                          options=["完全不了解", "略有耳闻", "比较了解", "非常熟悉"])
ai_conf = st.select_slider("7️⃣ 您认为自己识别“AI 生成新闻”的能力如何？", 
                          options=["完全无法识别", "较难识别", "一般", "较强识别力", "非常有信心"])

# ============================================================
# 📚 第三部分：Media Literacy (媒介素养)
# ============================================================
st.header("三、媒介素养评估")
st.write("请评价以下陈述与您的符合程度（1=非常不符合，5=非常符合）：")
ml_q1 = st.slider("8️⃣ 我在转发新闻前，通常会核实其来源的可靠性。", 1, 5, 3)
ml_q2 = st.slider("9️⃣ 我能轻易辨别出体育新闻中“标题党”的夸张成分。", 1, 5, 3)
ml_q3 = st.slider("🔟 我知道如何验证一条新闻的真伪（如搜索、查官方号）。", 1, 5, 3)
ml_q4 = st.slider("11️⃣ 我会关注不同媒体对同一体育事件的不同报道。", 1, 5, 3)

# ============================================================
# 📰 第四部分：新闻评价（核心：真假判断 + 查证意愿）
# ============================================================
st.header("四、体育新闻感知打分")
st.markdown("---")

responses = []
for i, row in df_questions.iterrows():
    slug = str(row.get("ID", i))
    title = str(row.get("title", "（标题缺失）"))

    st.subheader(f"案例 {i+1}")
    st.info(f"**【新闻标题】**：{title}")

    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        score = st.select_slider(
            f"Q1：您认为该标题的真实性评分 (1-10分)",
            options=list(range(1, 11)), value=5, key=f"s_{slug}"
        )
        # [新增] 查证意愿 (Verification Intent)
        v_intent = st.slider(
            f"Q2：如果您在网上看到该新闻，多大可能会去进一步查证？",
            1, 5, 3, key=f"v_{slug}", help="1=完全不会，5=一定会"
        )
    
    with col_b:
        # [修改] 话术更规范
        judgment = st.radio(
            f"Q3：基于您的直觉，您认为：",
            ["我认为是真实新闻", "我认为是虚假新闻", "无法判断"],
            key=f"j_{slug}"
        )

    responses.append({
        "ID": slug,
        "title": title,
        "score_truth": score,
        "judgment": judgment,
        "v_intent": v_intent
    })
    st.markdown("---")

# ============================================================
# 🔘 第五部分：对比与整体评价
# ============================================================
st.header("五、整体评价")
titles = [f"案例{i+1}: {r['title'][:15]}..." for i, r in enumerate(responses)]
hesitant_news = st.selectbox("12️⃣ 哪条新闻的真实性最让您**迟疑**？", titles)
clickbait_news = st.selectbox("13️⃣ 哪条新闻的标题最像“**标题党**”？", titles + ["均不像"])

overall_diff = st.select_slider("14️⃣ 判断这组新闻的真伪对您来说难度如何？", 
                              options=["非常容易", "比较容易", "一般", "比较困难", "非常困难"])
overall_conf = st.select_slider("15️⃣ 您对刚才给出的所有判断结果有多大信心？", 
                              options=["没信心", "信心较低", "一般", "比较有信心", "极有信心"])

# ============================================================
# 🚀 提交数据
# ============================================================
if st.button("提交问卷 Submit ✅", type="primary"):
    respondent_uuid = str(uuid.uuid4())
    all_success = True
    
    with st.spinner("正在安全上传数据..."):
        for r in responses:
            payload = {
                "respondent_uuid": respondent_uuid,
                "questionnaire_id": qid,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "age": age,
                "education": edu,
                "news_freq": freq,
                "sports_knowledge": sports_knowledge, # 新增
                "ai_usage": ai_use,
                "ai_knowledge": ai_know,
                "ai_confidence": ai_conf,
                "ml_score": (ml_q1 + ml_q2 + ml_q3 + ml_q4) / 4,
                "news_id": r["ID"],
                "news_title": r["title"],
                "score_truth": r["score_truth"],
                "judgment_cat": r["judgment"],
                "v_intent": r["v_intent"], # 新增
                "hesitant_news": hesitant_news,
                "clickbait_news": clickbait_news,
                "overall_difficulty": overall_diff,
                "overall_confidence": overall_conf
            }

            try:
                res = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
                if res.status_code != 200: all_success = False
            except:
                all_success = False

    # ===== 本地备份 =====
    out_file = "survey_responses_final.csv"
    # 将所有回答展平保存
    full_data = []
    for r in responses:
        # 复制 payload 的结构并填入当前新闻的数据
        row_data = payload.copy()
        row_data.update({"news_id": r["ID"], "news_title": r["title"], 
                         "score_truth": r["score_truth"], "judgment_cat": r["judgment"], 
                         "v_intent": r["v_intent"]})
        full_data.append(row_data)
    
    backup_df = pd.DataFrame(full_data)
    if not os.path.exists(out_file):
        backup_df.to_csv(out_file, index=False, encoding="utf-8-sig")
    else:
        backup_df.to_csv(out_file, index=False, mode="a", header=False, encoding="utf-8-sig")

    if all_success:
        st.success("🎉 提交成功！非常感谢您的参与。")
        st.balloons()
    else:
        st.warning("⚠️ 数据已记录在本地服务器，但未能同步至 Google Sheets。")
