# ============================================================
# 📘 体育新闻感知研究问卷系统（顺序循环问卷 + Google Sheets 上传每条新闻打分）
# ============================================================

import streamlit as st
import pandas as pd
import datetime, os, uuid, requests

# ✅ 你的 Google Apps Script Web App 地址
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzFJpJGK_pMcbRNzNFgLCl-dTLusdEXF_n03ElTiSpX7iCqebLtWFvPHPpcu4mPKxAyyQ/exec"

st.set_page_config(page_title="体育新闻感知研究问卷", layout="wide")

# 问卷文件目录
QUESTION_DIR = "./generated_questionnaires"
files = sorted([f for f in os.listdir(QUESTION_DIR) if f.endswith('.xlsx')])
if not files:
    st.error("❌ 未检测到问卷文件，请确认 /generated_questionnaires/ 下存在问卷文件。")
    st.stop()

# ========== 函数：确定当前应分配哪一份问卷 ==========
def get_current_questionnaire():
    if not os.path.exists("responses.csv"):
        return files[0]
    df = pd.read_csv("responses.csv")
    count_by_qid = df.groupby("questionnaire_id")["respondent_uuid"].nunique().to_dict()
    for f in files:
        qid = os.path.splitext(f)[0].replace("questionnaire_", "")
        filled = count_by_qid.get(qid, 0)
        if filled < 20:
            return f
    return files[0]  # 全部满 20 份则重新循环

# ========== 页面内容 ==========
st.title("体育新闻感知研究问卷")
st.markdown("""
您好！我们正在研究**体育新闻的吸引力与真实性感知**，
系统会依次分配问卷，每份问卷收集满20份后自动切换下一份。
感谢您的参与！
""")
agree = st.checkbox("我已理解并同意参与")
if not agree:
    st.stop()

# 选择当前问卷（按顺序）
chosen_file = get_current_questionnaire()
file_path = os.path.join(QUESTION_DIR, chosen_file)
df_questions = pd.read_excel(file_path)
qid = os.path.splitext(chosen_file)[0].replace("questionnaire_", "")
st.markdown(f"**当前问卷编号：{qid}**（文件：{chosen_file}）")
st.write(f"（本问卷包含 {len(df_questions)} 条新闻）")

# ====== 基本信息 ======
st.header("一、基本信息")
age = st.radio("1. 您的年龄？", ["18-25岁", "26-35岁", "36-45岁", "46岁以上"], key="age")
edu = st.radio("2. 教育程度：", ["高中及以下", "大专", "本科", "硕士及以上"], key="edu")
freq = st.radio("3. 您每周阅读到体育新闻的频率？", ["<1次", "1-3次", "4-7次", ">7次"], key="freq")

if freq == "<1次":
    st.warning("感谢您的参与！由于您阅读体育新闻频率较低，问卷到此结束。")
    st.stop()

# ====== 新闻评价部分 ======
st.header("二、体育新闻评价")
responses = []
for i, row in df_questions.iterrows():
    slug = str(row.get("ID", i))
    st.subheader(f"新闻 {slug}")
    st.write(row.get("title", "（缺失标题）"))
    score = st.radio(
        "您认为该体育新闻的真实性如何？",
        options=list(range(1, 11)),
        format_func=lambda x: f"{x}分",
        horizontal=True,
        key=f"radio_{qid}_{slug}"
    )
    responses.append({"ID": slug, "title": row.get("title", ""), "score_truth": score})

# ====== 选择题替代开放题 ======
st.header("三、选择题（基于前述新闻）")
titles = [f"新闻 {r['ID']}：{r['title']}" for r in responses]

hesitant_news = st.selectbox("4. 哪条新闻的真实性最让您迟疑？", titles, key="hesitant")
verify_news = st.selectbox("5. 是否有某条新闻让您强烈想验证真假？", titles, key="verify")
clickbait_news = st.selectbox("6. 哪条新闻的标题最像“标题党”？", titles + ["无"], key="clickbait")

# ====== 提交问卷 ======
if st.button("提交问卷"):
    all_success = True
    respondent_uuid = str(uuid.uuid4())
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
        except:
            all_success = False

    # 本地 CSV 备份
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
        st.success("✅ 数据已成功上传到 Google Sheets！")
    else:
        st.warning("⚠️ 上传部分数据失败，请检查网络或 Apps Script 配置。")
    st.info("系统已将每条新闻打分上传至 Google Sheets，并保存在本地备份。")

