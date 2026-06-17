# ============================================================
# 📘 体育新闻感知研究问卷系统（升级版 - 包含媒介素养与 AI 评估）
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
# 🧩 随机分配问卷（保证会话内一致）
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

# ================= 研究声明 =================
st.info("""
📌 **研究声明 / Research Statement**
本研究旨在探究读者对体育新闻真实性的感知及其影响因素。问卷采用匿名方式，数据仅用于学术研究。
某些新闻标题可能包含虚构或改写成分，不代表现实事实。
""")

agree = st.checkbox("我已阅读并同意参与本研究 / I agree to participate")
if not agree:
    st.stop()

# ============================================================
# 👤 第一部分：基本信息
# ============================================================
st.header("一、基本信息")
col1, col2 = st.columns(2)
with col1:
    age = st.radio("1️⃣ 您的年龄？", ["18-25岁", "26-35岁", "36-45岁", "46岁以上"])
    edu = st.radio("2️⃣ 您的教育程度？", ["高中及以下", "大专", "本科", "硕士及以上"])
with col2:
    freq = st.radio("3️⃣ 您每周阅读体育新闻的频率？", ["<1次", "1-3次", "4-7次", ">7次"])

if freq == "<1次":
    st.warning("感谢您的参与！由于您阅读体育新闻频率较低，本研究暂时不需要您的数据。")
    st.stop()

# ============================================================
# 🤖 第二部分：AI Familiarity (AI 熟悉度)
# ============================================================
st.header("二、AI 熟悉度")
ai_use = st.radio("4️⃣ 您是否使用过 ChatGPT 或类似的生成式 AI 工具？", ["从不使用", "偶尔使用", "经常使用"])
ai_know = st.select_slider("5️⃣ 您对“生成式 AI (AIGC)”制作文本内容的了解程度？", 
                          options=["完全不了解", "略有耳闻", "比较了解", "非常熟悉"])
ai_conf = st.select_slider("6️⃣ 您认为自己识别“AI 生成的新闻”的能力如何？", 
                          options=["完全无法识别", "较难识别", "一般", "较强识别力", "非常有信心"])

# ============================================================
# 📚 第三部分：Media Literacy (媒介素养 - 5题 Likert)
# ============================================================
st.header("三、媒介素养自我评估")
st.write("请评价以下陈述与您的符合程度（1=非常不符合，5=非常符合）：")

ml_q1 = st.slider("7️⃣ 我在转发新闻前，通常会核实其来源的可靠性。", 1, 5, 3)
ml_q2 = st.slider("8️⃣ 我能轻易辨别出体育新闻中“标题党”的夸张成分。", 1, 5, 3)
ml_q3 = st.slider("9️⃣ 我知道如何通过搜索引擎或其他渠道验证一条新闻的真伪。", 1, 5, 3)
ml_q4 = st.slider("🔟 我会关注不同媒体对同一体育事件的不同报道。", 1, 5, 3)
ml_q5 = st.slider("11️⃣ 我认为自己对体育行业背景有足够的了解，能判断新闻的合理性。", 1, 5, 3)

# ============================================================
# 📰 第四部分：新闻评价（核心环节：真假判断 + 评分）
# ============================================================
st.header("四、体育新闻感知打分")
st.markdown("---")

responses = []

for i, row in df_questions.iterrows():
    slug = str(row.get("ID", i))
    title = str(row.get("title", "（标题缺失）"))

    st.subheader(f"新闻案例 {i+1}")
    st.info(f"**标题：{title}**")

    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        score = st.select_slider(
            f"Q1：您认为该新闻的**真实性评分** (1-10分)",
            options=list(range(1, 11)),
            value=5,
            key=f"score_{slug}"
        )
    
    with col_b:
        judgment = st.radio(
            f"Q2：您认为这条新闻：",
            ["真实", "虚假", "无法判断"],
            key=f"judge_{slug}"
        )

    responses.append({
        "ID": slug,
        "title": title,
        "score_truth": score,
        "judgment": judgment
    })
    st.markdown("---")

# ============================================================
# 🔘 第五部分：选择题
# ============================================================
st.header("五、对比评价")
titles = [f"案例{i+1}: {r['title'][:20]}..." for i, r in enumerate(responses)]

hesitant_news = st.selectbox("12️⃣ 哪条新闻的真实性最让你**迟疑/纠结**？", titles)
verify_news = st.selectbox("13️⃣ 哪条新闻最让你产生**去搜索验证**的欲望？", titles)
clickbait_news = st.selectbox("14️⃣ 哪条新闻的标题最像“**标题党**”？", titles + ["均不像"])

# ============================================================
# 📊 第六部分：整体评价
# ============================================================
st.header("六、整体感官")
overall_truth = st.select_slider("15️⃣ 整体来看，您觉得这组新闻的真实比例高吗？", 
                               options=["非常低", "较低", "一半一半", "较高", "非常高"])
overall_diff = st.select_slider("16️⃣ 判断这组新闻的真伪对您来说：", 
                              options=["非常容易", "比较容易", "一般", "比较困难", "非常困难"])
overall_conf = st.select_slider("17️⃣ 您对刚才给出的判断结果有多大信心？", 
                              options=["没信心", "信心较低", "一般", "比较有信心", "极有信心"])

# ============================================================
# 🚀 提交数据
# ============================================================
if st.button("提交问卷 Submit ✅", type="primary"):
    respondent_uuid = str(uuid.uuid4())
    all_success = True
    
    with st.spinner("正在上传数据，请稍候..."):
        for r in responses:
            # 构建完整数据负载
            payload = {
                "respondent_uuid": respondent_uuid,
                "questionnaire_id": qid,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                # 基本信息
                "age": age,
                "education": edu,
                "news_freq": freq,
                # AI熟悉度
                "ai_usage": ai_use,
                "ai_knowledge": ai_know,
                "ai_confidence": ai_conf,
                # 媒介素养
                "ml_verify": ml_q1,
                "ml_clickbait": ml_q2,
                "ml_tools": ml_q3,
                "ml_compare": ml_q4,
                "ml_knowledge": ml_q5,
                # 新闻个体评价
                "news_id": r["ID"],
                "news_title": r["title"],
                "score_truth": r["score_truth"],
                "judgment_cat": r["judgment"],
                # 对比与整体
                "hesitant_news": hesitant_news,
                "verify_news": verify_news,
                "clickbait_news": clickbait_news,
                "overall_truth_sense": overall_truth,
                "overall_difficulty": overall_diff,
                "overall_confidence": overall_conf
            }

            try:
                res = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
                if res.status_code != 200:
                    all_success = False
            except Exception as e:
                all_success = False
                print(f"Error: {e}")

    # ===== 本地备份 =====
    out_file = "all_responses_backup.csv"
    backup_df = pd.DataFrame([payload]) # 这里仅存最后一条作为结构参考，实际应存所有
    # 为了本地备份完整，重新生成 responses 列表的 DataFrame
    full_resp_df = pd.DataFrame([ {**payload, "news_id": r["ID"], "news_title": r["title"], "score_truth": r["score_truth"], "judgment_cat": r["judgment"]} for r in responses ])
    
    if not os.path.exists(out_file):
        full_resp_df.to_csv(out_file, index=False, encoding="utf-8-sig")
    else:
        full_resp_df.to_csv(out_file, index=False, mode="a", header=False, encoding="utf-8-sig")

    if all_success:
        st.success("🎉 提交成功！非常感谢您为学术研究做出的贡献。")
        st.balloons()
        st.stop()
    else:
        st.warning("⚠️ 远程数据上传失败（可能是由于 Google 服务连接波动），但您的回答已保存在本地备份中。")
