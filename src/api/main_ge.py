from fastapi import FastAPI
from functools import lru_cache
import pandas as pd
from pathlib import Path

app = FastAPI(title="Tech Trends API (GE)")

# ==============================
# PATHS
# ==============================

BASE_DIR = Path(__file__).resolve().parents[2]

TREND_PATH = BASE_DIR / "src" / "data" / "processed" / "trend_ge.parquet"
LAG_PATH = BASE_DIR / "src" / "data" / "time_lag" / "time_lag_ge.csv"


# ==============================
# LOADERS
# ==============================

@lru_cache()
def load_trend() -> pd.DataFrame:
    if not TREND_PATH.exists():
        print("❌ trend_ge.parquet not found")
        return pd.DataFrame()

    try:
        df = pd.read_parquet(TREND_PATH)
    except Exception as e:
        print("❌ parquet read error:", e)
        return pd.DataFrame()

    if "topic_name" not in df.columns:
        print("❌ topic_name missing")
        return pd.DataFrame()

    # ✅ FIX: добавлена очистка как в semiconductors
    df = df.replace([float("inf"), float("-inf")], pd.NA)
    df = df.fillna(0)

    return df


@lru_cache()
def load_lag() -> pd.DataFrame:
    if not LAG_PATH.exists():
        print("❌ time_lag_ge.csv not found")
        return pd.DataFrame()

    try:
        df = pd.read_csv(LAG_PATH)
    except Exception as e:
        print("❌ csv read error:", e)
        return pd.DataFrame()

    return df


# ==============================
# HEALTH
# ==============================

@app.get("/health")
def health():
    return {"status": "ok", "domain": "gene_engineering"}


# ==============================
# TOPICS
# ==============================

@app.get("/topics")
def get_topics():
    df = load_trend()

    if df.empty:
        return []

    return sorted(df["topic_name"].dropna().astype(str).unique().tolist())


# ==============================
# TOPIC CARD (FIXED)
# ==============================

@app.get("/topic_card")
def get_topic(topic: str):
    df = load_trend()

    if df.empty:
        return []

    try:
        if "month" not in df.columns:
            return []

        df["month"] = pd.to_datetime(df["month"], errors="coerce")
        df = df.dropna(subset=["month"])

        # ✅ FIX 1: сохраняем полный df
        df_full = df.copy()

        df_topic = df[
            df["topic_name"]
            .astype(str)
            .str.contains(topic, case=False, na=False, regex=False)
        ]

        if df_topic.empty:
            return []

        # ✅ FIX 2: очистка (критично для trend_score)
        df_topic = df_topic.replace([float("inf"), float("-inf")], pd.NA)
        df_topic = df_topic.fillna(0)

        df_topic = df_topic.sort_values("month").tail(24)

        # ✅ FIX 3: глобальные патенты (НЕ по topic)
        total_patents = float(df_full["patents_count"].sum())

        df_topic = df_topic.copy()
        df_topic["total_patents"] = total_patents

        return df_topic.to_dict(orient="records")

    except Exception as e:
        print("ERROR /topic_card:", e)
        return []


# ==============================
# LAG STATS
# ==============================

@app.get("/lag_stats")
def lag_stats():
    df = load_lag()

    if df.empty or "lag_years" not in df.columns:
        return {}

    return {
        "mean": float(df["lag_years"].mean()),
        "median": float(df["lag_years"].median()),
        "min": float(df["lag_years"].min()),
        "max": float(df["lag_years"].max()),
        "count": int(len(df)),
    }


# ==============================
# LAG DISTRIBUTION
# ==============================

@app.get("/lag_distribution")
def lag_distribution():
    df = load_lag()

    if df.empty or "lag_years" not in df.columns:
        return {}

    bins = [0, 2, 5, 10, 15]
    labels = ["0-2", "2-5", "5-10", "10-15"]

    df["range"] = pd.cut(df["lag_years"], bins=bins, labels=labels)

    return df["range"].value_counts().sort_index().to_dict()

