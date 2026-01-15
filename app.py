# ============================================================
# 📘 体育新闻感知研究问卷系统（随机分配问卷 + Google Sheets 上传）
# ============================================================

import streamlit as st
import pandas as pd
import datetime, os, uuid, requests, zipfile, random

# ✅ Google Apps Script Web App 地址
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzFJpJGK_pMcbRNzNFgLCl-dTLusdEXF_n03ElTiSpX7iCqebLtWFvPHPpcu4mPKxAyyQ/exec"

# ✅ Streamlit 页面设置
st.set_page_config(page_title="体育新闻感知研究问卷", layout="wide")

# ============================================================
# 🗂️ 自动解压问卷文件
# ============================================================
if os.path.exists("generated_questionnaires.zip") and not os.path.exists("generated_questionnaires"):
    with zipfile.ZipFile("generated_questionnaires.zip", "r") as zip_ref:
        zip_ref.extractall("generated_questionnaires")

# ============================================================
# 📁 检查问卷文件
# ============================================================
QUESTION_DIR = "./generated_questionnaires"
if not os.path.exists(QUESTION_DIR):
    st.error("❌ 未检测到问卷文件，请检查 generated_questionnaires.zip。")
    st.stop()

files = sorted([f for f in os.listdir(QUESTION_DIR) if f.endswith(".xlsx")])
if not files:
    st.error("❌ 问卷文件夹为空，请检查问卷文件。")
    st.stop()

# ============================================================
# 🧩 随机分配问卷（每位被试一次）
# ============================================================
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

# ================= 研究声明（论文标准） =================
st.info("""
📌 **研究声明（请仔细阅读）**

本问卷为学术研究用途，旨在探究读者对体育新闻真实性的主观感知。
问卷中所呈现的新闻标题可能包含夸张、改写或虚构成分，仅用于研究目的，
不代表真实新闻报道。

您的参与完全自愿，所有数据将以匿名形式收集，仅用于学术分析，
不会涉及任何个人身份识别信息。

继续作答即表示您已阅读并同意参与本研究。
""")

st.info("""
📌 **Research Participation Statement**

This survey is conducted solely for academic research purposes and aims to examine
readers’ perceived credibility of sports news headlines.
Some news items may contain exaggerated, modified, or fictional elements
and do not represent real news reports.

Your participation is voluntary. All responses are collected anonymously
and will be used exclusively for academic analysis.

By continuing, you indicate that you have read and agreed to participate in this study.
""")

agree = st.checkbox("我已阅读并同意上述研究声明 / I agree to participate in this study")
if not agree:
    st.stop()

# ============================================================
# 👤 一、基本信息
# ============================================================
st.header("一、基本信息")

age = st.radio("1️⃣ 您的年龄？", ["18-25岁", "26-35岁", "36-45岁", "46岁以上"])
edu = st.radio("2️⃣ 您的教育程度？", ["高中及以下", "大专", "本科", "硕士及以上"])
freq = st.radio("3️⃣ 您每周阅读体育新闻的频率？", ["<1次", "1-3次", "4-7次", ">7次"])

if freq == "<1次":
    st.warning("感谢您的参与！由于您阅读体育新闻频率较低，问卷到此结束。")
    st.stop()

# ============================================================
# 📰 二、体育新闻真实性打分
# ============================================================
st.header("二、体育新闻真实性打分")

responses = []

for i, row in df_questions.iterrows():
    slug = str(row.get("ID", i))
    title = str(row.get("title", "（标题缺失）"))

    st.subheader(f"新闻 {slug}")
    st.write(title)

    score = st.radio(
        "您认为该体育新闻的真实性如何？",
        options=list(range(1, 11)),
        format_func=lambda x: f"{x}分",
        horizontal=True,
        key=f"score_{slug}"
    )

    responses.append({
        "ID": slug,
        "title": title,
        "score_truth": score
    })

# ============================================================
# 🔘 三、选择题
# ============================================================
st.header("三、选择题（基于上述新闻）")

titles = [f"新闻 {r['ID']}：{r['title']}" for r in responses]

hesitant_news = st.selectbox("4️⃣ 哪条新闻的真实性最让您迟疑？", titles)
verify_news = st.selectbox("5️⃣ 哪条新闻让您最想去验证真假？", titles)
clickbait_news = st.selectbox("6️⃣ 哪条新闻的标题最像“标题党”？", titles + ["无"])

# ============================================================
# 🚀 提交问卷
# ============================================================
if st.button("提交问卷 ✅"):
    respondent_uuid = str(uuid.uuid4())
    all_success = True

    for r in responses:
        payload = {
            "news_id": r["ID"],
            "title": r["title"],
            "score_truth": r["score_truth"],
            "questionnaire_id": qid,
            "age": age,
            "education": edu,
            "freq": freq,
            "hesitant_news": hesitant_news,
            "verify_news": verify_news,
            "clickbait_news": clickbait_news,
            "respondent_uuid": respondent_uuid
        }

        try:
            res = requests.post(GOOGLE_SCRIPT_URL, json=payload)
            if res.status_code != 200:
                all_success = False
        except Exception:
            all_success = False

    # ===== 本地 CSV 备份 =====
    out_file = "responses.csv"
    resp_df = pd.DataFrame(responses)
    resp_df["questionnaire_id"] = qid
    resp_df["age"] = age
    resp_df["education"] = edu
    resp_df["freq"] = freq
    resp_df["hesitant_news"] = hesitant_news
    resp_df["verify_news"] = verify_news
    resp_df["clickbait_news"] = clickbait_news
    resp_df["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resp_df["respondent_uuid"] = respondent_uuid

    if not os.path.exists(out_file):
        resp_df.to_csv(out_file, index=False, encoding="utf-8")
    else:
        resp_df.to_csv(out_file, index=False, mode="a", header=False, encoding="utf-8")

    if all_success:
        st.success("✅ 数据已成功提交，感谢您的参与！")
    else:
        st.warning("⚠️ 数据提交过程中出现问题，请检查网络或服务器设置。")
