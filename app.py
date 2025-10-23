import streamlit as st
import pandas as pd
import os
import uuid
import datetime
import requests
import zipfile

# ================== 配置 ==================
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzFJpJGK_pMcbRNzNFgLCl-dTLusdEXF_n03ElTiSpX7iCqebLtWFvPHPpcu4mPKxAyyQ/exec"
QUESTIONNAIRES_ZIP = "generated_questionnaires.zip"
QUESTION_DIR = "generated_questionnaires"

# ================== 初始化问卷目录 ==================
if not os.path.exists(QUESTION_DIR):
    if os.path.exists(QUESTIONNAIRES_ZIP):
        with zipfile.ZipFile(QUESTIONNAIRES_ZIP, 'r') as zip_ref:
            zip_ref.extractall(QUESTION_DIR)
        st.info("📂 已解压问卷文件")
    else:
        st.error("❌ 未找到问卷文件或 generated_questionnaires.zip")
        st.stop()

files = sorted([f for f in os.listdir(QUESTION_DIR) if f.endswith('.xlsx')])
if not files:
    st.error("❌ 未检测到 Excel 问卷文件")
    st.stop()

# ================== 页面 ==================
st.set_page_config(page_title="体育新闻感知研究问卷", layout="wide")
st.title("体育新闻感知研究问卷")
st.markdown(
    "您好！我们正在研究**体育新闻的吸引力与真实性感知**，系统会依次分配问卷，每份问卷收集满20份后自动切换下一份。感谢您的参与！"
)

agree = st.checkbox("我已理解并同意参与")
if not agree:
    st.stop()

# ================== 问卷选择逻辑 ==================
def get_current_questionnaire():
    # 读取本地 responses.csv（如果存在）统计完成数量
    count_by_qid = {}
    csv_file = "responses.csv"
    if os.path.exists(csv_file):
        df_resp = pd.read_csv(csv_file)
        count_by_qid = df_resp.groupby("questionnaire_id")["respondent_uuid"].nunique().to_dict()
    for f in files:
        qid = os.path.splitext(f)[0].replace("questionnaire_", "")
        filled = count_by_qid.get(qid, 0)
        if filled < 20:
            return f
    return files[0]  # 全部满 20 份则循环

chosen_file = get_current_questionnaire()
file_path = os.path.join(QUESTION_DIR, chosen_file)
df_questions = pd.read_excel(file_path)
qid = os.path.splitext(chosen_file)[0].replace("questionnaire_", "")

st.markdown(f"**当前问卷编号：{qid}**（文件：{chosen_file}）")
st.write(f"（本问卷包含 {len(df_questions)} 条新闻）")

# ================== 基本信息 ==================
st.header("一、基本信息")
age = st.radio("1. 您的年龄？", ["18-25岁", "26-35岁", "36-45岁", "46岁以上"], key="age")
edu = st.radio("2. 教育程度：", ["高中及以下", "大专", "本科", "硕士及以上"], key="edu")
freq = st.radio("3. 您每周阅读到体育新闻的频率？", ["<1次", "1-3次", "4-7次", ">7次"], key="freq")

if freq == "<1次":
    st.warning("感谢您的参与！由于您阅读体育新闻频率较低，问卷到此结束。")
    st.stop()

# ================== 新闻评价 ==================
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

# ================== 选择题 ==================
st.header("三、选择题（基于前述新闻）")
titles = [f"新闻 {r['ID']}：{r['title']}" for r in responses]

hesitant_news = st.selectbox("4. 哪条新闻的真实性最让您迟疑？", titles, key="hesitant")
verify_news = st.selectbox("5. 是否有某条新闻让您强烈想验证真假？", titles, key="verify")
clickbait_news = st.selectbox("6. 哪条新闻的标题最像“标题党”？", titles + ["无"], key="clickbait")

# ================== 提交 ==================
if st.button("提交问卷"):
    resp_df = pd.DataFrame(responses)
    resp_df["questionnaire_id"] = qid
    resp_df["age"] = age
    resp_df["education"] = edu
    resp_df["freq"] = freq
    resp_df["hesitant_news"] = hesitant_news
    resp_df["verify_news"] = verify_news
    resp_df["clickbait_news"] = clickbait_news
    resp_df["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resp_df["respondent_uuid"] = str(uuid.uuid4())

    # 上传到 Google Sheets
    payload = {
        "questionnaire_id": qid,
        "age": age,
        "education": edu,
        "freq": freq,
        "hesitant_news": hesitant_news,
        "verify_news": verify_news,
        "clickbait_news": clickbait_news,
        "respondent_uuid": str(uuid.uuid4())
    }
    try:
        requests.post(GOOGLE_SCRIPT_URL, json=payload)
        st.success("✅ 数据已成功上传到 Google Sheets！")
    except Exception as e:
        st.warning(f"⚠️ 上传到 Google Sheets 失败：{e}")

    # 本地备份 CSV（可选）
    out_file = "responses.csv"
    if not os.path.exists(out_file):
        resp_df.to_csv(out_file, index=False, encoding="utf-8")
    else:
        resp_df.to_csv(out_file, index=False, mode="a", header=False, encoding="utf-8")

    st.success("✅ 感谢！您的回答已提交。")
    for key in list(st.session_state.keys()):
        del st.session_state[key]
