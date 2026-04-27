import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# ==============================
# CONFIG
# ==============================

st.set_page_config(layout="wide")
st.title("📊 Аналитика технологических трендов")

API_URL = "http://localhost:8001"


# ==============================
# SAFE REQUEST
# ==============================

def safe_request(endpoint: str, params: dict | None = None):
    try:
        url = f"{API_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=5)

        # важно — ловим ошибки API
        response.raise_for_status()

        return response.json()

    except Exception as e:
        st.error(f"Ошибка API: {e}")
        return None


# ==============================
# LOAD TOPICS
# ==============================

@st.cache_data
def load_topics():
    data = safe_request("/topics")
    return data if data else []


topics = load_topics()

if not topics:
    st.warning("Нет доступных тем (проверь API и pipeline)")
    st.stop()

topic = st.sidebar.selectbox("Выберите тему", topics)


# ==============================
# TABS
# ==============================

tab1, tab2 = st.tabs(["📈 Тренды", "⏱ Лаг"])


# ==============================
# TAB 1: ТРЕНДЫ
# ==============================

with tab1:

    data = safe_request("/topic_card", {"topic": topic})

    if not data:
        st.warning("Нет данных из API")
        st.stop()

    df = pd.DataFrame(data)

    # безопасность типов
    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    df["papers_count"] = pd.to_numeric(df["papers_count"], errors="coerce")
    df["patents_count"] = pd.to_numeric(df["patents_count"], errors="coerce")

    if "trend_score" not in df.columns:
        df["trend_score"] = 0

    df = df.dropna(subset=["month"])

    df_long = df.melt(
        id_vars=["month"],
        value_vars=["papers_count", "patents_count", "trend_score"],
        var_name="Метрика",
        value_name="Значение"
    )

    metric_map = {
        "papers_count": "Публикации",
        "patents_count": "Патенты",
        "trend_score": "Тренд"
    }

    df_long["Метрика"] = df_long["Метрика"].map(metric_map)

    fig = px.line(
        df_long,
        x="month",
        y="Значение",
        color="Метрика",
        title=f"Динамика: {topic}"
    )

    st.plotly_chart(fig, use_container_width=True)


# ==============================
# TAB 2: LAG
# ==============================

with tab2:

    stats = safe_request("/lag_stats")

    if not stats:
        st.warning("Нет данных по лагам")
    else:
        col1, col2, col3 = st.columns(3)

        col1.metric("Медиана", round(stats.get("median", 0), 2))
        col2.metric("Среднее", round(stats.get("mean", 0), 2))
        col3.metric("Макс", round(stats.get("max", 0), 2))

        dist = safe_request("/lag_distribution")

        if dist:
            df_dist = pd.DataFrame({
                "Диапазон": list(dist.keys()),
                "Количество": list(dist.values())
            })

            fig = px.bar(
                df_dist,
                x="Диапазон",
                y="Количество",
                title="Распределение лагов"
            )

            st.plotly_chart(fig, use_container_width=True)

