import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import timedelta

# ==============================
# CONFIG
# ==============================

st.set_page_config(layout="wide")
st.title("📊 Аналитика технологических трендов")

API_URL = "http://localhost:8001"

# ==============================
# LOAD
# ==============================

@st.cache_data
def load_topics():
    return requests.get(f"{API_URL}/topics").json()

@st.cache_data
def load_topic_data(topic):
    return requests.get(f"{API_URL}/topic_card?topic={topic}").json()

@st.cache_data
def load_lag_stats():
    return requests.get(f"{API_URL}/lag_stats").json()

@st.cache_data
def load_lag_distribution():
    return requests.get(f"{API_URL}/lag_distribution").json()

# ==============================
# SIDEBAR
# ==============================

topics = load_topics()
selected_topic = st.sidebar.selectbox("Выберите тему", topics)

data = load_topic_data(selected_topic)

if not data:
    st.warning("Нет данных")
    st.stop()

df = pd.DataFrame(data)
df["month"] = pd.to_datetime(df["month"])
df = df.sort_values("month")

# ==============================
# KPI РАСЧЕТЫ 
# ==============================

last_month = df["month"].max()

df_3m = df[df["month"] >= last_month - pd.DateOffset(months=3)]
df_12m = df[df["month"] >= last_month - pd.DateOffset(months=12)]

# --- PAPERS ---
papers_total = df["papers_count"].sum()
papers_3m = df_3m["papers_count"].sum()
papers_12m = df_12m["papers_count"].sum()

papers_growth_3m = (papers_3m / papers_12m - 1) if papers_12m > 0 else 0
papers_mom = df["papers_count"].pct_change().iloc[-1]
papers_acc = df["papers_count"].pct_change().diff().iloc[-1]

# --- PATENTS (без дублирования) ---
df_unique = df[["month", "patents_count"]].drop_duplicates()

df_pat_3m = df_unique[df_unique["month"] >= last_month - pd.DateOffset(months=3)]
df_pat_12m = df_unique[df_unique["month"] >= last_month - pd.DateOffset(months=12)]

patents_total = df_unique["patents_count"].sum()
patents_3m = df_pat_3m["patents_count"].sum()
patents_12m = df_pat_12m["patents_count"].sum()

patents_growth_3m = (patents_3m / patents_12m - 1) if patents_12m > 0 else 0

# ==============================
# ВЕРХНИЙ БЛОК
# ==============================

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Рост публикаций")
    st.metric("90 дней", f"{papers_growth_3m*100:.1f}%")
    st.caption(f"MoM: {papers_mom*100:.1f}% | Ускорение: {papers_acc*100:.1f}%")
    st.caption(f"Всего: {int(papers_total):,}")

with col2:
    st.markdown("### Рост патентов")
    st.metric("90 дней", f"{patents_growth_3m*100:.1f}%")
    st.caption(f"За год: {patents_12m:,.0f}")
    st.caption(f"Всего: {int(patents_total):,}")

with col3:
    st.markdown("### Ключевые метрики")
    st.metric("Trend Score", f"{df['trend_score'].iloc[-1]*100:.0f}/100")
    st.caption(f"Состояние: {df['trend_label'].iloc[-1]}")

# ==============================
# KPI КАРТОЧКИ 
# ==============================

col1, col2, col3, col4 = st.columns(4)

col1.metric("Публикации", int(papers_total))
col2.metric("Патенты", int(patents_total))

lag_stats = load_lag_stats()
lag_median = lag_stats.get("median", 0)

col3.metric("Time Lag", f"{lag_median:.1f} года")
col4.metric("Trend Score", f"{df['trend_score'].iloc[-1]*100:.0f}/100")

# ==============================
# TABS (НЕ ТРОГАЛ)
# ==============================

tab1, tab2 = st.tabs(["Тренды", "Time Lag"])

# ==============================
# TAB 1 — ТРЕНДЫ
# ==============================

with tab1:
    fig = px.line(
        df,
        x="month",
        y=["papers_count", "patents_count", "trend_score"],
        title=f"Динамика: {selected_topic}"
    )
    st.plotly_chart(fig, use_container_width=True)

# ==============================
# TAB 2 — LAG
# ==============================

with tab2:

    # --- BAR DISTRIBUTION (у тебя уже было) ---
    lag_dist = load_lag_distribution()

    if lag_dist:
        lag_df = pd.DataFrame({
            "range": list(lag_dist.keys()),
            "count": list(lag_dist.values())
        })

        fig_bar = px.bar(
            lag_df,
            x="range",
            y="count",
            title="Распределение временного лага"
        )

        st.plotly_chart(fig_bar, use_container_width=True)

    # --- HISTOGRAM + MEDIAN (ДОБАВЛЕНО) ---
    try:
        lag_full = pd.read_csv("src/data/time_lag/time_lag.csv")

        fig_hist = px.histogram(lag_full, x="lag_years", nbins=20)

        median = lag_full["lag_years"].median()

        fig_hist.add_vline(
            x=median,
            line_dash="dash",
            annotation_text=f"Median: {median:.1f}",
            annotation_position="top right"
        )

        st.plotly_chart(fig_hist, use_container_width=True)

    except:
        st.warning("Нет данных для гистограммы")
