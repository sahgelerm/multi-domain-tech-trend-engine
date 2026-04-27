from fastapi import FastAPI
from functools import lru_cache
import pandas as pd
from pathlib import Path

app = FastAPI(title="Tech Trends API")

# ==============================
# PATHS
# ==============================

BASE_DIR = Path(__file__).resolve().parents[2]

TREND_PATH = BASE_DIR / "data" / "processed" / "trend.parquet"
LAG_PATH = BASE_DIR / "data" / "time_lag" / "time_lag.csv"


# ==============================
# LOADERS
# ==============================

@lru_cache()
def load_trend() -> pd.DataFrame:
    if not TREND_PATH.exists():
        print("❌ trend.parquet not found")
        return pd.DataFrame()

    try:
        df = pd.read_parquet(TREND_PATH)
    except Exception as e:
        print("❌ parquet read error:", e)
        return pd.DataFrame()

    if "topic_name" not in df.columns:
        print("❌ topic_name missing")
        return pd.DataFrame()

    return df


@lru_cache()
def load_lag() -> pd.DataFrame:
    if not LAG_PATH.exists():
        print("❌ time_lag.csv not found")
        return pd.DataFrame()

    try:
        return pd.read_csv(LAG_PATH)
    except Exception as e:
        print("❌ csv read error:", e)
        return pd.DataFrame()


# ==============================
# HEALTH
# ==============================

@app.get("/health")
def health():
    return {"status": "ok"}


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
# TOPIC CARD (СТАБИЛЬНО)
# ==============================

@app.get("/topic_card")
def get_topic(topic: str):
    df = load_trend()

    if df.empty:
        return []

    try:
        # фильтр (без regex)
        df = df[
            df["topic_name"]
            .astype(str)
            .str.contains(topic, case=False, na=False, regex=False)
        ]

        if df.empty:
            return []

        if "month" not in df.columns:
            return []

        # дата
        df["month"] = pd.to_datetime(df["month"], errors="coerce")
        df = df.dropna(subset=["month"])

        # КЛЮЧЕВОЙ ФИКС
        df = df.replace([float("inf"), float("-inf")], pd.NA)
        df = df.fillna(0)

        df = df.sort_values("month").tail(24)

        return df.to_dict(orient="records")

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

