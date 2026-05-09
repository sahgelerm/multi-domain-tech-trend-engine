import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# ==============================
# CONFIG
# ==============================

st.set_page_config(layout="wide")
st.title("📊 Аналитика технологических трендов (Генная инженерия)")

# API_URL = "http://localhost:8002"
# для Docker
API_URL = "http://api_gene_engineering:8002"



# ==============================
# SAFE REQUEST
# ==============================

def safe_request(endpoint: str, params: dict | None = None):
    try:
        url = f"{API_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Ошибка API: {e}")
        return None


# ==============================
# LOAD TOPICS
# ==============================

@st.cache_data(ttl=0)  # ✅ FIX 1: отключили кеш
def load_topics():
    data = safe_request("/topics")
    return data if data else []


# ✅ FIX 2: принудительная очистка кеша (важно)
st.cache_data.clear()

topics = load_topics()

if not topics:
    st.warning("Нет доступных тем")
    st.stop()

topic = st.sidebar.selectbox("Выберите тему", topics)


# ==============================
# TABS
# ==============================

tab1, tab2 = st.tabs(["📈 Тренды", "⏱ Лаг"])


# ==============================
# TAB 1
# ==============================

with tab1:

    data = safe_request("/topic_card", {"topic": topic})

    if not data:
        st.warning("Нет данных из API")
    else:
        df = pd.DataFrame(data)

        df["month"] = pd.to_datetime(df["month"], errors="coerce")
        df["papers_count"] = pd.to_numeric(df["papers_count"], errors="coerce")
        df["patents_count"] = pd.to_numeric(df["patents_count"], errors="coerce")

        # ✅ FIX 3: гарантируем отсутствие NaN
        df["trend_score"] = pd.to_numeric(
            df.get("trend_score", 0),
            errors="coerce"
        ).fillna(0)

        df = df.dropna(subset=["month"])

        if df.empty:
            st.warning("Нет валидных данных после обработки")
        else:
            last = df.iloc[-1]

            # ✅ FIX 4: безопасное получение total_patents
            if "total_patents" in df.columns and not df["total_patents"].isna().all():
                patents = int(df["total_patents"].iloc[0])
            else:
                patents = int(df["patents_count"].sum())

            papers = int(last["papers_count"])
            trend_score = float(last["trend_score"]) * 100

            lag_stats = safe_request("/lag_stats") or {}
            lag = lag_stats.get("median", 0)

            col1, col2, col3, col4 = st.columns(4)

            def card(title, value):
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #4facfe, #00f2fe);
                    padding: 20px;
                    border-radius: 12px;
                    color: white;
                    text-align: center;
                ">
                    <div style="font-size:14px;">{title}</div>
                    <div style="font-size:28px; font-weight:bold;">{value}</div>
                </div>
                """, unsafe_allow_html=True)

            with col1:
                card("Публикации", f"{papers:,}")

            with col2:
                card("Патенты", f"{patents:,}")

            with col3:
                card("Time Lag", f"{round(lag,1)} года")

            with col4:
                card("Trend Score", f"{int(trend_score)}/100")

            df_plot = df[["month", "papers_count", "patents_count", "trend_score"]].melt(
                id_vars="month",
                var_name="Метрика",
                value_name="Значение"
            )

            metric_map = {
                "papers_count": "Публикации",
                "patents_count": "Патенты",
                "trend_score": "Тренд"
            }

            df_plot["Метрика"] = df_plot["Метрика"].map(metric_map)

            fig = px.line(
                df_plot,
                x="month",
                y="Значение",
                color="Метрика",
                title=f"Динамика развития: {topic}"
            )

            st.plotly_chart(fig, width="stretch")


# ==============================
# TAB 2
# ==============================

with tab2:

    stats = safe_request("/lag_stats")

    if stats:
        col1, col2, col3 = st.columns(3)

        col1.metric("Медиана", round(stats.get("median", 0), 2))
        col2.metric("Среднее", round(stats.get("mean", 0), 2))
        col3.metric("Макс", round(stats.get("max", 0), 2))
    else:
        st.warning("Нет данных по лагу")

    dist = safe_request("/lag_distribution")

    if dist:
        df_dist = pd.DataFrame({
            "Лаг (лет)": list(dist.keys()),
            "Количество": list(dist.values())
        })

        fig = px.bar(
            df_dist,
            x="Лаг (лет)",
            y="Количество",
            title="Распределение временного лага"
        )

        st.plotly_chart(fig, width="stretch")
    else:
        st.warning("Нет распределения лага")

