import pandas as pd
from pathlib import Path

from src.analytics.trend.metrics import TrendMetrics

# ==============================
# PATHS
# ==============================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_PATH = BASE_DIR / "data" / "processed" / "trend_ge.parquet"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "trend_score_ge.csv"

# ==============================
# LOAD
# ==============================

def load_data() -> pd.DataFrame:

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"trend_ge.parquet not found: {INPUT_PATH}"
        )

    df = pd.read_parquet(INPUT_PATH)

    required_cols = [
        "topic_name",
        "month",
        "papers_count",
        "patents_count"
    ]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"{col} missing in input data")

    return df


# ==============================
# RUN
# ==============================

def run():

    print("=== TREND SCORE GE START ===")

    df = load_data()

    # ==============================
    # COMPUTE
    # ==============================

    df = TrendMetrics(df).compute()

    # ==============================
    # EXPORT
    # ==============================

    export_cols = [
        "topic_name",
        "month",
        "papers_count",
        "patents_count",
        "trend_score",
        "trend_label"
    ]

    df_export = df[export_cols].copy()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df_export.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved → {OUTPUT_PATH}")
    print("=== DONE ===")


if __name__ == "__main__":
    run()
