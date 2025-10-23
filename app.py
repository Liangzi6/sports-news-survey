import streamlit as st
import pandas as pd
import uuid
import datetime
import requests

# -------------------------------
# 假设你已经有新闻数据 DataFrame
# columns: ID, title, content
# -------------------------------
news_df = pd.DataFrame([
    {"ID": "F11", "title": "新闻 F11：运气彻底坍塌？", "content": "新闻内容1"},
    {"ID": "F10", "title": "新闻 F10：海港夺冠不可能！", "content": "新闻内容2"},
    {"ID": "F1",  "title": "新闻 F1：亚泰连胜北上广只差最后一战", "content": "新闻内容3"},
    {"ID": "F2",  "title": "新闻 F2：蒿俊闵怒斥四不奉陪", "content": "新闻内容4"},
    {"ID": "F12", "title": "新闻 F12：凤凰大爆炸", "content": "新闻内容5"},
])

# 页面标题
st.title("新闻打分问卷")

# 基础信息
age = st.selectbox("年龄", ["18-25岁", "26-35岁", "36-45岁", "46岁以上"])
education = st.selectbox("学历", ["高中及以下", "本科", "硕士及以上"])
freq = st.selectbox("获取新闻频率", ["1-3次", "4-7次", "8次以上"])
questionnaire_id = "问卷001"

# 收集打分
st.subheader("请对以下新闻进行评分（1-10分）")
responses = []

for i, row in news_df.iterrows():
    score = st.slider(
        f"{row['title']}",  # 显示新闻标题
        min_value=1,
        max_value=10,
        value=5,
        key=f"score_{row['ID']}_{i}"  # 确保 key 唯一
    )
    responses.append({
        "news_id": row["ID"],
        "title": row["title"],
        "score_truth": score
    })

# 提交按钮
if st.button("提交问卷"):
    respondent_uuid = str(uuid.uuid4())
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 给每条新闻加上问卷信息
    for r in responses:
        r.update({
            "age": age,
            "education": education,
            "freq": freq,
            "questionnaire_id": questionnaire_id,
            "timestamp": timestamp,
            "respondent_uuid": respondent_uuid
        })

    # 上传到 Google Sheet (示例使用 requests.post)
    sheet_url = "你的 Google Sheet 接口 URL"  # 替换成实际接口
    success_count = 0
    for r in responses:
        try:
            resp = requests.post(sheet_url, json=r)
            if resp.status_code == 200:
                success_count += 1
        except Exception as e:
            st.error(f"上传失败: {e}")

    # 本地保存 CSV 备份
    df_backup = pd.DataFrame(responses)
    backup_filename = f"responses_backup_{respondent_uuid}.csv"
    df_backup.to_csv(backup_filename, index=False, encoding="utf-8-sig")

    st.success(f"提交成功！{success_count}/{len(responses)} 条新闻已上传，备份文件: {backup_filename}")
