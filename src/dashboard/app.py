import streamlit as st
import pandas as pd
import requests
import plotly.express as px

API_URL = "http://localhost:8000"

st.set_page_config(layout="wide")
st.title("Tech Trend Dashboard")

# Получаем список топиков
@st.cache_data
def load_topics():
    df = pd.read_parquet("data/processed/trend.parquet")
    return sorted(df["topic_name"].dropna().unique())

topics = load_topics()

topic = st.sidebar.selectbox("Select Topic", topics)

# Запрос к API
response = requests.get(
    f"{API_URL}/topic_card",
    params={"topic": topic}
)

data = response.json()

df = pd.DataFrame(data)

# Charts
st.subheader("Papers over time")
fig1 = px.line(df, x="month", y="papers_count")
st.plotly_chart(fig1, use_container_width=True)

st.subheader("Patents over time")
fig2 = px.line(df, x="month", y="patents_count")
st.plotly_chart(fig2, use_container_width=True)

