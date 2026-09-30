# ============================================================
# 🏟️ AI-Generated Sports News Detection
# Experiment 2 — Randomized Pretest-Intervention-Posttest Study
# ============================================================

import streamlit as st
import pandas as pd
import datetime
import os
import uuid
import requests
import zipfile
import random
import hashlib

# ============================================================
# 0. CONFIGURATION
# ============================================================

GOOGLE_SCRIPT_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbzFJpJGK_pMcbRNzNFgLCl-dTLusdEXF_n03ElTiSpX7iCqebLtWFvPHPpcu4mPKxAyyQ"
    "/exec"
)

QUESTION_DIR = "./generated_questionnaires"

# Number of news stimuli in each test
PRETEST_N = 12
POSTTEST_N = 12

# Balanced real / AI-generated stimuli
REAL_PER_TEST = 6
AI_PER_TEST = 6

# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="体育新闻真实性研究",
    page_icon="🏟️",
    layout="wide"
)

# ============================================================
# 2. LOAD QUESTIONNAIRE FILES
# ============================================================

if (
    os.path.exists("generated_questionnaires.zip")
    and not os.path.exists("generated_questionnaires")
):
    with zipfile.ZipFile(
        "generated_questionnaires.zip",
        "r"
    ) as zip_ref:
        zip_ref.extractall("generated_questionnaires")

if (
    not os.path.exists(QUESTION_DIR)
    or not os.listdir(QUESTION_DIR)
):
    st.error(
        "❌ 未检测到 generated_questionnaires 文件夹或问卷文件。"
    )
    st.stop()

files = sorted(
    [
        f for f in os.listdir(QUESTION_DIR)
        if f.lower().endswith(".xlsx")
    ]
)

if len(files) < 2:
    st.error(
        "❌ 至少需要 2 个 Excel 问卷文件，"
        "以保证前测和后测可以使用不同的刺激材料。"
    )
    st.stop()


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def normalize_label(value):
    """
    Convert different possible label formats into:
    real / ai / unknown
    """

    if pd.isna(value):
        return None

    s = str(value).strip().lower()

    real_values = {
        "real",
        "true",
        "real news",
        "真实",
        "真实新闻",
        "真",
        "1",
        "real_news"
    }

    ai_values = {
        "ai",
        "fake",
        "false",
        "fake news",
        "ai-generated",
        "ai generated",
        "ai-generated news",
        "人工智能生成",
        "ai生成",
        "ai生成新闻",
        "虚假",
        "虚假新闻",
        "假",
        "0",
        "ai_news"
    }

    if s in real_values:
        return "real"

    if s in ai_values:
        return "ai"

    if "ai" in s and "real" not in s:
        return "ai"

    if "生成" in s:
        return "ai"

    if "真实" in s:
        return "real"

    if "虚假" in s:
        return "ai"

    return None


def find_column(df, candidates):
    """
    Find the first matching column from candidate names.
    """

    lower_map = {
        str(c).strip().lower(): c
        for c in df.columns
    }

    for candidate in candidates:
        key = candidate.strip().lower()

        if key in lower_map:
            return lower_map[key]

    # Partial matching
    for c in df.columns:
        c_lower = str(c).strip().lower()

        for candidate in candidates:
            if candidate.strip().lower() in c_lower:
                return c

    return None


def load_excel(path):
    """
    Load one Excel stimulus file and normalize important columns.
    """

    df = pd.read_excel(path)

    id_col = find_column(
        df,
        [
            "ID",
            "id",
            "news_id",
            "News_ID",
            "stimulus_id",
            "item_id"
        ]
    )

    title_col = find_column(
        df,
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
        df,
        [
            "truth_label",
            "truth",
            "label",
            "answer",
            "correct_answer",
            "category",
            "type",
            "真实标签"
        ]
    )

    if id_col is None:
        # Create IDs if not provided
        df["__generated_id"] = [
            f"stimulus_{i+1:04d}"
            for i in range(len(df))
        ]
        id_col = "__generated_id"

    if title_col is None:
        raise ValueError(
            f"文件 {os.path.basename(path)} "
            "中没有找到标题列。请使用 title / news_title / headline 等列名。"
        )

    if label_col is None:
        raise ValueError(
            f"文件 {os.path.basename(path)} "
            "中没有找到真实标签列。\n\n"
            "请增加 truth_label 列，并使用 real / ai 两类标签。"
        )

    result = df.copy()

    result["__id"] = result[id_col].astype(str)
    result["__title"] = result[title_col].astype(str)
    result["__truth"] = result[label_col].apply(normalize_label)

    # Optional metadata columns
    optional_columns = [
        "topic",
        "source",
        "source_type",
        "generation_method",
        "difficulty",
        "sport",
        "year"
    ]

    for col in optional_columns:
        actual = find_column(df, [col])

        if actual is not None:
            result[f"__{col}"] = result[actual].astype(str)
        else:
            result[f"__{col}"] = ""

    result = result[
        result["__title"].notna()
        & result["__truth"].isin(["real", "ai"])
    ].copy()

    return result


def load_all_files():
    """
    Load all Excel files.
    """

    all_data = {}

    for f in files:
        path = os.path.join(
            QUESTION_DIR,
            f
        )

        try:
            df = load_excel(path)

            all_data[f] = df

        except Exception as e:
            st.warning(
                f"⚠️ 文件 {f} 无法正常读取：{e}"
            )

    return all_data


def choose_two_stimulus_sets(all_data):
    """
    Choose two different Excel files for pre-test and post-test.

    Each file should contain at least:
    6 real + 6 AI items.

    Pre-test and post-test must not share stimulus IDs.
    """

    candidates = []

    for fname, df in all_data.items():

        real_df = df[
            df["__truth"] == "real"
        ]

        ai_df = df[
            df["__truth"] == "ai"
        ]

        if (
            len(real_df) >= REAL_PER_TEST
            and len(ai_df) >= AI_PER_TEST
        ):
            candidates.append(
                (
                    fname,
                    real_df,
                    ai_df
                )
            )

    if len(candidates) < 2:
        raise ValueError(
            "目前没有找到至少两个可以用于前测/后测的 Excel 文件。\n\n"
            "每个文件至少需要：\n"
            "6 条 real + 6 条 ai"
        )

    # Shuffle candidate order
    shuffled = candidates.copy()
    random.shuffle(shuffled)

    for i in range(len(shuffled)):

        pre_name, pre_real, pre_ai = shuffled[i]

        pre_ids = set(
            pre_real["__id"].tolist()
            + pre_ai["__id"].tolist()
        )

        for j in range(len(shuffled)):

            if i == j:
                continue

            post_name, post_real, post_ai = shuffled[j]

            post_ids = set(
                post_real["__id"].tolist()
                + post_ai["__id"].tolist()
            )

            # No overlap
            if pre_ids.isdisjoint(post_ids):

                pre_real_sample = pre_real.sample(
                    n=REAL_PER_TEST
                )

                pre_ai_sample = pre_ai.sample(
                    n=AI_PER_TEST
                )

                post_real_sample = post_real.sample(
                    n=REAL_PER_TEST
                )

                post_ai_sample = post_ai.sample(
                    n=AI_PER_TEST
                )

                pre_df = pd.concat(
                    [
                        pre_real_sample,
                        pre_ai_sample
                    ],
                    ignore_index=True
                )

                post_df = pd.concat(
                    [
                        post_real_sample,
                        post_ai_sample
                    ],
                    ignore_index=True
                )

                pre_df = pre_df.sample(
                    frac=1
                ).reset_index(drop=True)

                post_df = post_df.sample(
                    frac=1
                ).reset_index(drop=True)

                return (
                    pre_name,
                    post_name,
                    pre_df,
                    post_df
                )

    raise ValueError(
        "无法找到刺激 ID 完全不重复的前测/后测文件组合。"
    )


def send_payload(payload):
    """
    Upload one record to Google Apps Script.
    """

    try:

        response = requests.post(
            GOOGLE_SCRIPT_URL,
            json=payload,
            timeout=15
        )

        return response.status_code == 200

    except Exception:
        return False


def append_local_backup(records):
    """
    Save local CSV backup.
    """

    if not records:
        return

    out_file = "survey_responses_experiment2.csv"

    df = pd.DataFrame(records)

    if not os.path.exists(out_file):

        df.to_csv(
            out_file,
            index=False,
            encoding="utf-8-sig"
        )

    else:

        df.to_csv(
            out_file,
            index=False,
            mode="a",
            header=False,
            encoding="utf-8-sig"
        )


# ============================================================
# 4. INITIALIZE SESSION
# ============================================================

if "initialized" not in st.session_state:

    st.session_state.initialized = True

    st.session_state.respondent_uuid = str(
        uuid.uuid4()
    )

    st.session_state.group = random.choice(
        [
            "intervention",
            "control"
        ]
    )

    all_data = load_all_files()

    try:

        (
            pre_file,
            post_file,
            pre_df,
            post_df
        ) = choose_two_stimulus_sets(
            all_data
        )

        st.session_state.pre_file = pre_file
        st.session_state.post_file = post_file
        st.session_state.pre_df = pre_df
        st.session_state.post_df = post_df

    except Exception as e:

        st.error(
            f"❌ 刺激材料配置错误：\n\n{e}"
        )

        st.stop()

    st.session_state.start_time = (
        datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    st.session_state.phase = "consent"

    st.session_state.news_records = []

    st.session_state.intervention_records = []

    st.session_state.manipulation_records = []

    st.session_state.post_complete = False


# ============================================================
# 5. TITLE
# ============================================================

st.title(
    "🏟️ 体育新闻真实性与 AI 生成内容识别研究"
)

st.caption(
    "Research Study on Sports News Credibility "
    "and AI-Generated Content Detection"
)


# ============================================================
# 6. CONSENT
# ============================================================

if st.session_state.phase == "consent":

    st.header(
        "研究说明 / Participant Information"
    )

    st.info(
        """
本研究旨在了解人们阅读体育新闻时对新闻真实性的判断方式，
以及不同信息核验策略对新闻判断表现的影响。

本研究不会要求您提供姓名、身份证号码、电话号码、
银行卡信息或其他直接身份识别信息。

问卷结果仅用于科研分析。

部分新闻标题可能由人工智能生成，
也可能来自真实新闻材料。

在研究过程中，请尽量根据您当下的判断作答，
不要与其他参与者讨论答案。

完成整个研究大约需要 12–18 分钟。
        """
    )

    st.subheader(
        "参与同意"
    )

    consent = st.checkbox(
        "我已阅读以上说明，并自愿参加本研究。"
    )

    if consent:

        if st.button(
            "开始研究 →",
            type="primary"
        ):

            st.session_state.phase = "demographics"

            st.rerun()

    st.stop()


# ============================================================
# 7. DEMOGRAPHICS
# ============================================================

if st.session_state.phase == "demographics":

    st.header(
        "一、基本信息"
    )

    st.write(
        "以下信息仅用于统计分析。"
    )

    col1, col2 = st.columns(2)

    with col1:

        age = st.selectbox(
            "1. 您的年龄",
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
            "2. 您的性别",
            [
                "男",
                "女",
                "其他",
                "不愿回答"
            ]
        )

        education = st.selectbox(
            "3. 您的最高学历",
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
            "4. 您通常多频繁阅读体育新闻？",
            [
                "几乎不阅读",
                "每月1–3次",
                "每周1–3次",
                "每周4–6次",
                "几乎每天"
            ]
        )

        sports_knowledge = st.select_slider(
            "5. 您认为自己对体育赛事和体育新闻的了解程度如何？",
            options=[
                "完全不了解",
                "比较不了解",
                "一般",
                "比较了解",
                "非常了解"
            ],
            value="一般"
        )

        social_news = st.selectbox(
            "6. 您主要通过什么渠道接触体育新闻？",
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

    st.session_state.demographics = {
        "age": age,
        "gender": gender,
        "education": education,
        "sports_freq": sports_freq,
        "sports_knowledge": sports_knowledge,
        "social_news": social_news
    }

    if st.button(
        "继续 →",
        type="primary"
    ):

        st.session_state.phase = "ai_literacy"

        st.rerun()

    st.stop()


# ============================================================
# 8. AI LITERACY
# ============================================================

if st.session_state.phase == "ai_literacy":

    st.header(
        "二、AI 使用与 AI 素养"
    )

    st.write(
        "请根据您平时的实际情况回答。"
    )

    ai_usage = st.selectbox(
        "7. 您使用 ChatGPT、Claude、Gemini、DeepSeek 或类似生成式 AI 工具的频率？",
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
        "8. 您对生成式 AI 工作原理的了解程度？",
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
        "9. 您以前是否接受过 AI、信息核验或媒介素养相关培训？",
        [
            "从未接受过",
            "接受过少量相关教育",
            "接受过课程/讲座",
            "接受过系统培训",
            "不确定"
        ]
    )

    st.subheader(
        "AI 素养自评"
    )

    st.write(
        "1 = 非常不同意，5 = 非常同意"
    )

    ai_items = [
        "10. 我了解生成式 AI 可以生成看起来像真实新闻的文本。",
        "11. 我了解 AI 生成文本可能包含看似合理但实际错误的信息。",
        "12. 我了解仅凭语言风格不能可靠判断一篇新闻是否由 AI 生成。",
        "13. 我知道可以通过新闻来源和外部证据核验信息。",
        "14. 我知道 AI 生成内容检测工具本身也可能产生错误。",
        "15. 我能够解释为什么一篇看起来可信的新闻仍然需要进一步核验。"
    ]

    ai_scores = []

    for item in ai_items:

        ai_scores.append(
            st.slider(
                item,
                1,
                5,
                3,
                key=item
            )
        )

    st.session_state.ai_literacy = {
        "ai_usage": ai_usage,
        "ai_knowledge": ai_knowledge,
        "ai_training": ai_training,
        "ai_item_scores": ai_scores,
        "ai_literacy_mean": sum(ai_scores) / len(ai_scores)
    }

    if st.button(
        "继续 →",
        type="primary"
    ):

        st.session_state.phase = "media_literacy"

        st.rerun()

    st.stop()


# ============================================================
# 9. MEDIA / NEWS LITERACY
# ============================================================

if st.session_state.phase == "media_literacy":

    st.header(
        "三、新闻与媒介素养"
    )

    st.write(
        """
下面的陈述描述的是您平时阅读、判断和核验新闻时的行为。
请根据您平时的实际情况回答。

1 = 非常不同意
2 = 不同意
3 = 一般
4 = 同意
5 = 非常同意
"""
    )

    media_items = [

        # Source evaluation
        "16. 我会关注一条新闻来自哪个媒体或信息来源。",
        "17. 在相信一条新闻之前，我会考虑信息来源是否可靠。",
        "18. 即使新闻标题看起来可信，我也会关注发布者和来源。",

        # Evidence verification
        "19. 当一条新闻的重要信息缺少证据时，我会进一步查证。",
        "20. 我知道如何利用搜索引擎或官方网站核验新闻中的关键事实。",
        "21. 如果新闻涉及具体人物、时间、地点或数字，我会尝试核对这些信息。",

        # Cross-source comparison
        "22. 对重要新闻，我会查看不止一个信息来源。",
        "23. 当不同媒体对同一事件的报道存在差异时，我会进行比较。",
        "24. 我不会仅因为多个网站都出现相同内容，就认为信息一定真实。",

        # Critical interpretation
        "25. 我会注意新闻是否使用夸张、煽动性或过度确定的表达。",
        "26. 我会区分新闻报道中的事实、观点和推测。",
        "27. 当我无法获得足够证据时，我愿意暂时保持不确定。"
    ]

    media_scores = []

    for item in media_items:

        media_scores.append(
            st.slider(
                item,
                1,
                5,
                3,
                key=item
            )
        )

    st.session_state.media_literacy = {
        f"ml_{i+1}": score
        for i, score in enumerate(media_scores)
    }

    st.session_state.media_literacy[
        "media_literacy_mean"
    ] = sum(media_scores) / len(media_scores)

    if st.button(
        "进入新闻判断测试 →",
        type="primary"
    ):

        st.session_state.phase = "pretest"

        st.rerun()

    st.stop()


# ============================================================
# 10. NEWS EVALUATION FUNCTION
# ============================================================

def render_news_test(
    df,
    phase_name
):

    st.header(
        "四、新闻真实性判断"
        if phase_name == "pretest"
        else "七、第二轮新闻真实性判断"
    )

    if phase_name == "pretest":

        st.info(
            """
接下来您将看到若干体育新闻标题。

请根据您当前掌握的信息进行判断。

重要提示：
- 不需要追求“聪明的猜测”
- 如果您认为证据不足，可以选择“无法确定”
- 请尽量独立完成
- 不要搜索互联网
- 不要与其他参与者讨论
"""
        )

    else:

        st.info(
            """
现在是第二轮新闻判断。

请按照您平时会采用的方式独立判断这些新闻。
不要搜索互联网，也不要询问其他参与者。
"""
        )

    responses = []

    for i, (_, row) in enumerate(
        df.iterrows()
    ):

        stimulus_id = str(
            row["__id"]
        )

        title = str(
            row["__title"]
        )

        st.subheader(
            f"新闻 {i+1} / {len(df)}"
        )

        st.info(
            f"**新闻标题：**\n\n{title}"
        )

        judgment = st.radio(
            "A. 您认为这条新闻是：",
            [
                "真实新闻",
                "AI生成新闻",
                "无法确定"
            ],
            key=f"{phase_name}_judgment_{stimulus_id}"
        )

        confidence = st.slider(
            "B. 您对刚才判断的信心有多高？",
            1,
            5,
            3,
            key=f"{phase_name}_confidence_{stimulus_id}",
            help="1=完全没有信心，5=非常有信心"
        )

        verification = st.slider(
            "C. 如果您在现实中看到这条新闻，您有多大可能进一步核验？",
            1,
            5,
            3,
            key=f"{phase_name}_verification_{stimulus_id}",
            help="1=完全不会，5=一定会"
        )

        credibility = st.select_slider(
            "D. 从直觉上看，这条新闻有多真实？",
            options=list(range(1, 11)),
            value=5,
            key=f"{phase_name}_credibility_{stimulus_id}"
        )

        responses.append(
            {
                "stimulus_id": stimulus_id,
                "title": title,
                "truth_label": row["__truth"],
                "judgment": judgment,
                "confidence": confidence,
                "verification_intention": verification,
                "perceived_credibility": credibility,

                "topic": row["__topic"],
                "source": row["__source"],
                "source_type": row["__source_type"],
                "generation_method": row["__generation_method"],
                "difficulty": row["__difficulty"],
                "sport": row["__sport"],
                "year": row["__year"]
            }
        )

        st.markdown("---")

    return responses


# ============================================================
# 11. PRETEST
# ============================================================

if st.session_state.phase == "pretest":

    responses = render_news_test(
        st.session_state.pre_df,
        "pretest"
    )

    if st.button(
        "完成第一轮判断 →",
        type="primary"
    ):

        st.session_state.pretest_responses = responses

        st.session_state.phase = "randomization"

        st.rerun()

    st.stop()


# ============================================================
# 12. RANDOMIZATION
# ============================================================

if st.session_state.phase == "randomization":

    st.session_state.phase = "intervention"

    st.rerun()


# ============================================================
# 13. INTERVENTION
# ============================================================

if st.session_state.phase == "intervention":

    if st.session_state.group == "intervention":

        st.header(
            "五、新闻核验训练"
        )

        st.info(
            "下面是一份简短的新闻信息核验指导。"
        )

        st.markdown(
            """
## 新闻核验的基本原则

### ① 不要只依赖“读起来像不像真的”

一篇新闻的语言可能非常自然，
也可能由人工智能生成。

因此：

> **语言风格本身不是可靠的真实性证据。**

---

### ② 首先关注来源

看到一条重要新闻时，可以关注：

- 谁发布的？
- 来源是否明确？
- 是否存在真实媒体或机构？
- 原始报道在哪里？

---

### ③ 核验具体事实

特别关注：

- 人物姓名
- 比赛名称
- 比赛时间
- 比赛地点
- 比赛结果
- 统计数字
- 机构名称

这些信息通常比“文章读起来是否自然”更适合进行事实核验。

---

### ④ 进行交叉比较

如果一条新闻非常重要：

> 不要只看一个来源。

可以比较其他独立媒体、官方机构或赛事组织的信息。

---

### ⑤ 注意过度确定的表达

需要谨慎对待：

- “震惊全球”
- “彻底证明”
- “100%确定”
- “所有专家都认为”
- “史上第一次”

这些语言并不自动意味着新闻是假的，
但值得进一步核验。

---

### ⑥ 允许自己“不确定”

新闻判断不是一定要：

> 真 / 假

如果现有信息不足：

> **无法确定**

也是一种合理判断。

---

## 最重要的原则

> **先核验信息，再判断真实性。**

不要因为一条新闻：

> “看起来很像 AI”

就直接认为它是 AI 生成。

也不要因为：

> “读起来很专业”

就直接认为它是真实新闻。
            """
        )

        intervention_check = st.slider(
            "请确认您已经阅读并理解以上新闻核验原则。",
            1,
            5,
            3,
            help="1=完全没有理解，5=完全理解"
        )

        useful = st.slider(
            "您认为以上核验原则对判断新闻真实性是否有帮助？",
            1,
            5,
            3
        )

        st.session_state.intervention_records = {
            "intervention_type": "verification_training",
            "intervention_understanding": intervention_check,
            "intervention_usefulness": useful
        }

    else:

        st.header(
            "五、体育新闻阅读材料"
        )

        st.info(
            "下面是一段与体育新闻阅读相关的背景材料。"
        )

        st.markdown(
            """
## 体育新闻阅读

体育新闻可以涉及比赛结果、运动员表现、
赛事背景、球队信息以及相关社会话题。

阅读体育新闻时，读者通常会关注：

- 比赛项目
- 运动员
- 比赛结果
- 赛事时间
- 比赛地点
- 新闻来源

体育新闻的标题通常需要在有限的篇幅中概括事件，
因此标题可能与完整新闻正文存在信息量上的差异。

阅读不同类型的体育新闻时，
可以结合自己的兴趣和已有知识理解新闻内容。
            """
        )

        attention = st.slider(
            "请评价您对以上材料的认真阅读程度。",
            1,
            5,
            3
        )

        st.session_state.intervention_records = {
            "intervention_type": "neutral_sports_reading",
            "intervention_understanding": attention,
            "intervention_usefulness": attention
        }

    if st.button(
        "继续 →",
        type="primary"
    ):

        st.session_state.phase = "manipulation_check"

        st.rerun()

    st.stop()


# ============================================================
# 14. MANIPULATION CHECK
# ============================================================

if st.session_state.phase == "manipulation_check":

    st.header(
        "六、阅读理解检查"
    )

    st.write(
        "以下问题用于了解您是否理解刚才阅读的内容。"
    )

    if st.session_state.group == "intervention":

        mc1 = st.radio(
            "1. 判断一条新闻是否由 AI 生成时，以下哪种做法最符合刚才的建议？",
            [
                "只根据语言风格判断",
                "只看标题是否专业",
                "先核验来源和具体事实",
                "只根据自己的第一印象"
            ]
        )

        mc2 = st.radio(
            "2. 如果没有足够证据确认新闻真实性，应该：",
            [
                "一定判断为真实",
                "一定判断为 AI",
                "可以选择暂时无法确定",
                "随机选择一个答案"
            ]
        )

        mc3 = st.radio(
            "3. 新闻写得很自然是否意味着它一定是真实新闻？",
            [
                "是",
                "不是"
            ]
        )

        manipulation_score = 0

        if mc1 == "先核验来源和具体事实":
            manipulation_score += 1

        if mc2 == "可以选择暂时无法确定":
            manipulation_score += 1

        if mc3 == "不是":
            manipulation_score += 1

    else:

        mc1 = st.radio(
            "1. 体育新闻通常可能包含哪些信息？",
            [
                "比赛结果和运动员信息",
                "只有娱乐内容",
                "只有广告",
                "只有天气信息"
            ]
        )

        mc2 = st.radio(
            "2. 体育新闻标题的主要作用通常是什么？",
            [
                "概括或吸引读者关注新闻内容",
                "保证新闻一定真实",
                "自动证明新闻来自 AI",
                "代替所有事实证据"
            ]
        )

        mc3 = st.radio(
            "3. 不同体育新闻可能关注同一事件的不同方面。",
            [
                "正确",
                "错误"
            ]
        )

        manipulation_score = 0

        if mc1 == "比赛结果和运动员信息":
            manipulation_score += 1

        if mc2 == "概括或吸引读者关注新闻内容":
            manipulation_score += 1

        if mc3 == "正确":
            manipulation_score += 1

    st.session_state.manipulation_records.update(
        {
            "mc_score": manipulation_score,
            "mc_total": 3
        }
    )

    if st.button(
        "进入第二轮新闻判断 →",
        type="primary"
    ):

        st.session_state.phase = "posttest"

        st.rerun()

    st.stop()


# ============================================================
# 15. POSTTEST
# ============================================================

if st.session_state.phase == "posttest":

    responses = render_news_test(
        st.session_state.post_df,
        "posttest"
    )

    if st.button(
        "完成第二轮判断 →",
        type="primary"
    ):

        st.session_state.posttest_responses = responses

        st.session_state.phase = "overall"

        st.rerun()

    st.stop()


# ============================================================
# 16. OVERALL EVALUATION
# ============================================================

if st.session_state.phase == "overall":

    st.header(
        "八、整体评价"
    )

    overall_difficulty = st.select_slider(
        "28. 判断这些新闻的真实性总体来说有多困难？",
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
        "29. 您对自己刚才所有新闻判断的总体信心如何？",
        options=[
            "完全没有信心",
            "信心较低",
            "一般",
            "比较有信心",
            "非常有信心"
        ],
        value="一般"
    )

    perceived_change = st.select_slider(
        "30. 与第一轮相比，您认为自己第二轮判断新闻真实性的方式是否发生变化？",
        options=[
            "明显没有变化",
            "略有变化",
            "有一些变化",
            "变化较大",
            "变化非常明显"
        ],
        value="有一些变化"
    )

    final_strategy = st.multiselect(
        "31. 完成研究后，您认为自己判断新闻真实性时最重要的因素包括哪些？",
        [
            "新闻来源",
            "具体事实",
            "多个媒体之间的比较",
            "语言表达方式",
            "标题风格",
            "自己的体育知识",
            "自己的第一印象",
            "其他"
        ]
    )

    comment = st.text_area(
        "32. 如果您愿意，可以留下对本研究的其他意见（可选）"
    )

    if st.button(
        "提交研究结果 ✅",
        type="primary"
    ):

        st.session_state.overall = {
            "overall_difficulty": overall_difficulty,
            "overall_confidence": overall_confidence,
            "perceived_change": perceived_change,
            "final_strategy": " | ".join(final_strategy),
            "comment": comment
        }

        st.session_state.phase = "submit"

        st.rerun()

    st.stop()


# ============================================================
# 17. SUBMISSION
# ============================================================

if st.session_state.phase == "submit":

    st.header(
        "正在保存研究结果"
    )

    participant_id = (
        st.session_state.respondent_uuid
    )

    timestamp = datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    base = {
        "respondent_uuid": participant_id,
        "timestamp": timestamp,

        # Experiment information
        "experiment": "Experiment_2",
        "group": st.session_state.group,

        # Stimulus sets
        "pretest_file": st.session_state.pre_file,
        "posttest_file": st.session_state.post_file,

        # Demographics
        **st.session_state.demographics,

        # AI literacy
        **{
            k: v
            for k, v in st.session_state.ai_literacy.items()
            if k != "ai_item_scores"
        },

        # Media literacy
        **st.session_state.media_literacy,

        # Intervention
        **st.session_state.intervention_records,

        # Manipulation check
        **st.session_state.manipulation_records,

        # Overall evaluation
        **st.session_state.overall
    }

    # Add individual AI literacy items
    for i, score in enumerate(
        st.session_state.ai_literacy[
            "ai_item_scores"
        ]
    ):
        base[
            f"ai_literacy_item_{i+1}"
        ] = score

    # ========================================================
    # Build trial-level records
    # ========================================================

    all_records = []

    for phase_name, responses in [
        (
            "pretest",
            st.session_state.pretest_responses
        ),
        (
            "posttest",
            st.session_state.posttest_responses
        )
    ]:

        for trial_index, r in enumerate(
            responses,
            start=1
        ):

            judgment_map = {
                "真实新闻": "real",
                "AI生成新闻": "ai",
                "无法确定": "uncertain"
            }

            judgment_normalized = (
                judgment_map[
                    r["judgment"]
                ]
            )

            correct = (
                1
                if judgment_normalized
                == r["truth_label"]
                else 0
            )

            uncertain = (
                1
                if judgment_normalized
                == "uncertain"
                else 0
            )

            record = {
                **base,

                "phase": phase_name,
                "trial_index": trial_index,

                "stimulus_id": r[
                    "stimulus_id"
                ],

                "news_title": r[
                    "title"
                ],

                "truth_label": r[
                    "truth_label"
                ],

                "judgment_raw": r[
                    "judgment"
                ],

                "judgment_normalized":
                    judgment_normalized,

                "correct": correct,

                "uncertain": uncertain,

                "confidence": r[
                    "confidence"
                ],

                "verification_intention":
                    r[
                        "verification_intention"
                    ],

                "perceived_credibility":
                    r[
                        "perceived_credibility"
                    ],

                "topic": r[
                    "topic"
                ],

                "source": r[
                    "source"
                ],

                "source_type": r[
                    "source_type"
                ],

                "generation_method": r[
                    "generation_method"
                ],

                "difficulty": r[
                    "difficulty"
                ],

                "sport": r[
                    "sport"
                ],

                "news_year": r[
                    "year"
                ]
            }

            all_records.append(
                record
            )

    # ========================================================
    # Upload
    # ========================================================

    success_count = 0

    progress = st.progress(
        0
    )

    for i, record in enumerate(
        all_records
    ):

        ok = send_payload(
            record
        )

        if ok:
            success_count += 1

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

    try:

        append_local_backup(
            all_records
        )

        local_backup_ok = True

    except Exception:

        local_backup_ok = False

    # ========================================================
    # Final result
    # ========================================================

    if success_count == len(
        all_records
    ):

        st.success(
            "🎉 研究结果已成功提交。"
        )

    elif success_count > 0:

        st.warning(
            f"⚠️ 部分数据已上传："
            f"{success_count}/{len(all_records)} 条。"
        )

    else:

        st.error(
            "⚠️ Google Sheets 同步失败。"
        )

    if local_backup_ok:

        st.info(
            "本地备份也已完成。"
        )

    else:

        st.warning(
            "本地备份写入失败，请检查服务器文件权限。"
        )

    st.success(
        """
感谢您参与本研究！

您的回答已经记录。

本研究不要求参与者提供姓名等直接身份信息。
研究数据将仅用于科研分析。
        """
    )

    st.info(
        f"Participant ID：{participant_id}"
    )

    st.stop()
