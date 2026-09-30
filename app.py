# ============================================================
# 🏟️ 体育新闻真实性与 AI 生成内容识别研究问卷
# Simple Offline Recruitment Version
# ============================================================

import streamlit as st
import pandas as pd
import datetime
import os
import uuid
import requests
import zipfile
import random


# ============================================================
# 1. CONFIG
# ============================================================

GOOGLE_SCRIPT_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbzFJpJGK_pMcbRNzNFgLCl-dTLusdEXF_n03ElTiSpX7iCqebLtWFvPHPpcu4mPKxAyyQ"
    "/exec"
)

QUESTION_DIR = "./generated_questionnaires"


# ============================================================
# 2. PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="体育新闻真实性研究",
    page_icon="🏟️",
    layout="wide"
)


# ============================================================
# 3. LOAD QUESTIONNAIRE FILES
# ============================================================

# Automatically extract ZIP if necessary
if (
    os.path.exists("generated_questionnaires.zip")
    and not os.path.exists("generated_questionnaires")
):
    with zipfile.ZipFile(
        "generated_questionnaires.zip",
        "r"
    ) as zip_ref:
        zip_ref.extractall("generated_questionnaires")


# Check folder
if (
    not os.path.exists(QUESTION_DIR)
    or not os.listdir(QUESTION_DIR)
):
    st.error(
        "❌ 未检测到问卷文件，请检查 generated_questionnaires 文件夹。"
    )
    st.stop()


# Find Excel files
files = sorted(
    [
        f for f in os.listdir(QUESTION_DIR)
        if f.lower().endswith(".xlsx")
    ]
)


if len(files) == 0:
    st.error(
        "❌ generated_questionnaires 文件夹中没有找到 Excel 文件。"
    )
    st.stop()


# ============================================================
# 4. RANDOMLY SELECT ONE QUESTIONNAIRE
# ============================================================

if "chosen_file" not in st.session_state:

    st.session_state.chosen_file = random.choice(files)


chosen_file = st.session_state.chosen_file

file_path = os.path.join(
    QUESTION_DIR,
    chosen_file
)


# ============================================================
# 5. READ QUESTIONNAIRE
# ============================================================

try:

    df_questions = pd.read_excel(
        file_path
    )

except Exception as e:

    st.error(
        f"❌ 无法读取问卷文件：{e}"
    )
    st.stop()


# ============================================================
# 6. FIND COLUMNS
# ============================================================

def find_column(df, candidates):

    # Exact match
    for candidate in candidates:

        if candidate in df.columns:
            return candidate

    # Case-insensitive match
    for col in df.columns:

        for candidate in candidates:

            if str(col).strip().lower() == str(
                candidate
            ).strip().lower():

                return col

    return None


id_col = find_column(
    df_questions,
    [
        "ID",
        "id",
        "news_id",
        "News_ID"
    ]
)


title_col = find_column(
    df_questions,
    [
        "title",
        "Title",
        "news_title",
        "headline",
        "Headline",
        "新闻标题",
        "标题"
    ]
)


label_col = find_column(
    df_questions,
    [
        "truth_label",
        "truth",
        "label",
        "answer",
        "correct_answer",
        "真实标签"
    ]
)


# ============================================================
# 7. BASIC COLUMN CHECK
# ============================================================

if title_col is None:

    st.error(
        """
❌ Excel 中没有找到新闻标题列。

请至少包含：

ID
title

例如：

| ID | title |
|---|---|
| N001 | 某球员获得冠军…… |
| N002 | 某球队宣布…… |
"""
    )

    st.stop()


# If no ID column, create one
if id_col is None:

    df_questions["ID"] = [
        f"N{i+1:03d}"
        for i in range(len(df_questions))
    ]

    id_col = "ID"


# If no truth label, still allow questionnaire to run
# This is useful for collecting pilot data.
if label_col is None:

    df_questions["truth_label"] = ""

    label_col = "truth_label"


# ============================================================
# 8. PARTICIPANT ID
# ============================================================

if "respondent_uuid" not in st.session_state:

    st.session_state.respondent_uuid = str(
        uuid.uuid4()
    )


respondent_uuid = st.session_state.respondent_uuid


# ============================================================
# 9. PAGE TITLE
# ============================================================

st.title(
    "🏟️ 体育新闻真实性与 AI 生成内容识别研究"
)

st.caption(
    "Research on Sports News Credibility "
    "and AI-Generated Content Detection"
)


# ============================================================
# 10. RESEARCH INFORMATION
# ============================================================

st.info(
    """
### 研究说明

本研究旨在了解人们阅读体育新闻时，
如何判断新闻内容的真实性，以及影响新闻判断的相关因素。

问卷采用匿名方式进行。

研究过程中可能会出现真实体育新闻和人工智能生成的新闻内容。
请根据您自己的第一印象和判断完成问卷。

本问卷没有“答题技巧”，
请尽量按照您真实的想法作答。

数据仅用于学术研究。
"""
)


# ============================================================
# 11. CONSENT
# ============================================================

agree = st.checkbox(
    "我已阅读以上说明，并自愿参加本研究。"
)


if not agree:

    st.warning(
        "请阅读研究说明并勾选同意后继续。"
    )

    st.stop()


# ============================================================
# 12. BASIC INFORMATION
# ============================================================

st.header(
    "一、基本信息"
)

st.write(
    "以下信息仅用于统计分析。"
)


col1, col2 = st.columns(2)


with col1:

    age = st.selectbox(
        "1️⃣ 您的年龄？",
        [
            "18–25岁",
            "26–35岁",
            "36–45岁",
            "46–55岁",
            "56岁及以上",
            "不愿回答"
        ]
    )


    gender = st.selectbox(
        "2️⃣ 您的性别？",
        [
            "男",
            "女",
            "其他",
            "不愿回答"
        ]
    )


    education = st.selectbox(
        "3️⃣ 您的最高学历？",
        [
            "高中及以下",
            "大专",
            "本科",
            "硕士",
            "博士及以上",
            "不愿回答"
        ]
    )


with col2:

    sports_freq = st.selectbox(
        "4️⃣ 您平时阅读体育新闻的频率？",
        [
            "几乎不阅读",
            "每月1–3次",
            "每周1–3次",
            "每周4–6次",
            "几乎每天"
        ]
    )


    sports_knowledge = st.select_slider(
        "5️⃣ 您认为自己对体育赛事和体育新闻的了解程度？",
        options=[
            "完全不了解",
            "比较不了解",
            "一般",
            "比较了解",
            "非常了解"
        ],
        value="一般"
    )


    news_channel = st.selectbox(
        "6️⃣ 您最常通过什么渠道接触体育新闻？",
        [
            "新闻网站/新闻客户端",
            "微信公众号/社交媒体",
            "短视频平台",
            "搜索引擎",
            "电视/广播",
            "朋友或群聊",
            "其他"
        ]
    )


# ============================================================
# 13. AI FAMILIARITY
# ============================================================

st.header(
    "二、AI 使用与熟悉程度"
)


ai_usage = st.selectbox(
    "7️⃣ 您使用 ChatGPT、Claude、Gemini、DeepSeek 等生成式 AI 工具的频率？",
    [
        "从未使用",
        "很少使用",
        "每月1–2次",
        "每周1–2次",
        "每周3次以上",
        "几乎每天"
    ]
)


ai_knowledge = st.select_slider(
    "8️⃣ 您认为自己对生成式 AI 生成文本内容的原理了解程度？",
    options=[
        "完全不了解",
        "略有了解",
        "一般",
        "比较了解",
        "非常了解"
    ],
    value="一般"
)


ai_training = st.selectbox(
    "9️⃣ 您以前是否接受过 AI、信息核验或媒介素养相关培训？",
    [
        "从未接受过",
        "接受过少量相关教育",
        "接受过课程或讲座",
        "接受过系统培训",
        "不确定"
    ]
)


# ============================================================
# 14. AI LITERACY
# ============================================================

st.subheader(
    "AI 素养自评"
)

st.write(
    "请根据您的实际情况评价以下陈述。"
)

st.caption(
    "1 = 非常不同意，5 = 非常同意"
)


ai_items = [

    "10️⃣ 我了解生成式 AI 可以生成看起来像真实新闻的文本。",

    "11️⃣ 我了解 AI 生成文本可能包含看似合理但实际错误的信息。",

    "12️⃣ 我了解仅凭语言风格不能可靠判断一篇新闻是否由 AI 生成。",

    "13️⃣ 我知道可以通过新闻来源和外部证据核验信息。",

    "14️⃣ 我知道 AI 生成内容检测工具本身也可能产生错误。",

    "15️⃣ 我能够解释为什么一篇看起来可信的新闻仍然需要进一步核验。"
]


ai_scores = []


for i, item in enumerate(ai_items):

    score = st.slider(
        item,
        1,
        5,
        3,
        key=f"ai_{i}"
    )

    ai_scores.append(score)


ai_literacy_mean = sum(
    ai_scores
) / len(ai_scores)


# ============================================================
# 15. MEDIA LITERACY
# ============================================================

st.header(
    "三、新闻与媒介素养"
)

st.write(
    """
请根据您平时阅读和判断新闻的实际情况回答。

1 = 非常不同意  
2 = 不同意  
3 = 一般  
4 = 同意  
5 = 非常同意
"""
)


media_items = [

    # Source evaluation
    "16️⃣ 我会关注一条新闻来自哪个媒体或信息来源。",

    "17️⃣ 在相信一条新闻之前，我会考虑信息来源是否可靠。",

    "18️⃣ 即使新闻标题看起来可信，我也会关注发布者和来源。",

    # Verification
    "19️⃣ 当一条新闻的重要信息缺少证据时，我会进一步查证。",

    "20️⃣ 我知道如何利用搜索引擎或官方网站核验新闻中的关键事实。",

    "21️⃣ 如果新闻涉及具体人物、时间、地点或数字，我会尝试核对这些信息。",

    # Cross-source
    "22️⃣ 对重要新闻，我会查看不止一个信息来源。",

    "23️⃣ 当不同媒体对同一事件的报道存在差异时，我会进行比较。",

    "24️⃣ 我不会仅因为多个网站都出现相同内容，就认为信息一定真实。",

    # Critical interpretation
    "25️⃣ 我会注意新闻是否使用夸张、煽动性或过度确定的表达。",

    "26️⃣ 我会区分新闻报道中的事实、观点和推测。",

    "27️⃣ 当我无法获得足够证据时，我愿意暂时保持不确定。"
]


media_scores = []


for i, item in enumerate(media_items):

    score = st.slider(
        item,
        1,
        5,
        3,
        key=f"ml_{i}"
    )

    media_scores.append(score)


media_literacy_mean = sum(
    media_scores
) / len(media_scores)


# ============================================================
# 16. NEWS EVALUATION
# ============================================================

st.header(
    "四、体育新闻真实性判断"
)

st.info(
    """
下面将显示若干体育新闻标题。

请根据您自己的判断进行评价。

如果您无法确定新闻是真实还是 AI 生成，
可以选择“无法确定”。

请不要搜索互联网，也不要与其他参与者讨论答案。
"""
)


responses = []


for i, row in df_questions.iterrows():

    news_id = str(
        row[id_col]
    )

    title = str(
        row[title_col]
    )


    st.subheader(
        f"案例 {i + 1}"
    )


    st.info(
        f"**【新闻标题】**\n\n{title}"
    )


    # --------------------------------------------------------
    # Judgment
    # --------------------------------------------------------

    judgment = st.radio(
        "A. 您认为这条新闻是：",
        [
            "真实新闻",
            "AI生成新闻",
            "无法确定"
        ],
        key=f"judgment_{news_id}"
    )


    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    confidence = st.slider(
        "B. 您对刚才判断的信心有多高？",
        1,
        5,
        3,
        key=f"confidence_{news_id}",
        help="1 = 完全没有信心，5 = 非常有信心"
    )


    # --------------------------------------------------------
    # Verification intention
    # --------------------------------------------------------

    verification = st.slider(
        "C. 如果您在现实中看到这条新闻，您有多大可能进一步核验？",
        1,
        5,
        3,
        key=f"verification_{news_id}",
        help="1 = 完全不会，5 = 一定会"
    )


    # --------------------------------------------------------
    # Perceived credibility
    # --------------------------------------------------------

    credibility = st.select_slider(
        "D. 从直觉上看，这条新闻有多真实？",
        options=list(range(1, 11)),
        value=5,
        key=f"credibility_{news_id}"
    )


    # --------------------------------------------------------
    # Save response
    # --------------------------------------------------------

    responses.append(
        {
            "news_id": news_id,
            "news_title": title,
            "truth_label": str(
                row[label_col]
            ),
            "judgment": judgment,
            "confidence": confidence,
            "verification_intention": verification,
            "perceived_credibility": credibility
        }
    )


    st.markdown("---")


# ============================================================
# 17. OVERALL EVALUATION
# ============================================================

st.header(
    "五、整体评价"
)


overall_difficulty = st.select_slider(
    "28️⃣ 判断这些新闻的真实性总体来说有多困难？",
    options=[
        "非常容易",
        "比较容易",
        "一般",
        "比较困难",
        "非常困难"
    ],
    value="一般"
)


overall_confidence = st.select_slider(
    "29️⃣ 您对刚才所有判断结果的总体信心如何？",
    options=[
        "完全没有信心",
        "信心较低",
        "一般",
        "比较有信心",
        "非常有信心"
    ],
    value="一般"
)


overall_strategy = st.multiselect(
    "30️⃣ 您在判断新闻真实性时主要考虑哪些因素？",
    [
        "新闻来源",
        "具体事实",
        "不同媒体之间的比较",
        "语言表达方式",
        "标题风格",
        "自己的体育知识",
        "自己的第一印象",
        "AI生成内容的语言特征",
        "其他"
    ]
)


additional_comment = st.text_area(
    "31️⃣ 您是否有其他意见或建议？（可选）"
)


# ============================================================
# 18. SUBMIT
# ============================================================

st.markdown("---")


if st.button(
    "提交问卷 Submit ✅",
    type="primary"
):

    timestamp = datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # ========================================================
    # Participant-level information
    # ========================================================

    participant_info = {

        "respondent_uuid":
            respondent_uuid,

        "timestamp":
            timestamp,

        "questionnaire_file":
            chosen_file,

        # Basic information
        "age":
            age,

        "gender":
            gender,

        "education":
            education,

        "sports_freq":
            sports_freq,

        "sports_knowledge":
            sports_knowledge,

        "news_channel":
            news_channel,

        # AI familiarity
        "ai_usage":
            ai_usage,

        "ai_knowledge":
            ai_knowledge,

        "ai_training":
            ai_training,

        "ai_literacy_mean":
            ai_literacy_mean,

        # Media literacy
        "media_literacy_mean":
            media_literacy_mean,

        # Overall
        "overall_difficulty":
            overall_difficulty,

        "overall_confidence":
            overall_confidence,

        "overall_strategy":
            " | ".join(
                overall_strategy
            ),

        "additional_comment":
            additional_comment
    }


    # Add individual AI literacy items

    for i, score in enumerate(
        ai_scores
    ):

        participant_info[
            f"ai_literacy_item_{i + 1}"
        ] = score


    # Add individual media literacy items

    for i, score in enumerate(
        media_scores
    ):

        participant_info[
            f"media_literacy_item_{i + 1}"
        ] = score


    # ========================================================
    # Create trial-level records
    # ========================================================

    all_records = []


    for trial_number, r in enumerate(
        responses,
        start=1
    ):

        # Normalize judgment
        if r["judgment"] == "真实新闻":
            judgment_normalized = "real"

        elif r["judgment"] == "AI生成新闻":
            judgment_normalized = "ai"

        else:
            judgment_normalized = "uncertain"


        # Determine correctness if truth label exists
        truth = str(
            r["truth_label"]
        ).strip().lower()


        # Standardize possible labels
        if truth in [
            "real",
            "true",
            "真实",
            "真实新闻",
            "1"
        ]:

            truth_normalized = "real"

        elif truth in [
            "ai",
            "fake",
            "false",
            "虚假",
            "虚假新闻",
            "ai生成",
            "ai生成新闻",
            "0"
        ]:

            truth_normalized = "ai"

        else:

            truth_normalized = ""


        if truth_normalized != "":

            correct = int(
                judgment_normalized
                == truth_normalized
            )

        else:

            correct = ""


        uncertain = int(
            judgment_normalized
            == "uncertain"
        )


        record = {
            **participant_info,

            "trial_number":
                trial_number,

            "news_id":
                r["news_id"],

            "news_title":
                r["news_title"],

            "truth_label":
                truth_normalized,

            "judgment":
                judgment_normalized,

            "correct":
                correct,

            "uncertain":
                uncertain,

            "confidence":
                r["confidence"],

            "verification_intention":
                r["verification_intention"],

            "perceived_credibility":
                r["perceived_credibility"]
        }


        all_records.append(
            record
        )


    # ========================================================
    # Google Sheets upload
    # ========================================================

    success_count = 0


    progress = st.progress(
        0
    )


    for i, record in enumerate(
        all_records
    ):

        try:

            response = requests.post(
                GOOGLE_SCRIPT_URL,
                json=record,
                timeout=15
            )


            if response.status_code == 200:

                success_count += 1


        except Exception:

            pass


        progress.progress(
            int(
                (i + 1)
                / len(all_records)
                * 100
            )
        )


    # ========================================================
    # Local backup
    # ========================================================

    local_backup_ok = True

    try:

        backup_file = (
            "survey_responses_experiment2.csv"
        )


        backup_df = pd.DataFrame(
            all_records
        )


        if not os.path.exists(
            backup_file
        ):

            backup_df.to_csv(
                backup_file,
                index=False,
                encoding="utf-8-sig"
            )

        else:

            backup_df.to_csv(
                backup_file,
                index=False,
                mode="a",
                header=False,
                encoding="utf-8-sig"
            )


    except Exception:

        local_backup_ok = False


    # ========================================================
    # Result
    # ========================================================

    if success_count == len(
        all_records
    ):

        st.success(
            "🎉 问卷提交成功！感谢您的参与。"
        )

    elif success_count > 0:

        st.warning(
            f"⚠️ 部分数据上传成功："
            f"{success_count}/{len(all_records)} 条。"
        )

    else:

        st.warning(
            "⚠️ Google Sheets 暂时没有同步成功。"
        )


    if local_backup_ok:

        st.info(
            "✅ 本地备份已完成。"
        )


    st.success(
        """
感谢您参与本研究！

您的回答已经记录。
本研究数据仅用于学术研究。
        """
    )


    st.stop()
