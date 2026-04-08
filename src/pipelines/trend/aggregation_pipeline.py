import pandas as pd
from src.analytics.trend.metrics import TrendMetrics


INPUT_PATH = "data/processed/trend.parquet"
OUTPUT_PATH = "/home/ubuntu/OpenAlex/semiconductors_trend_enriched.parquet"


def load_data() -> pd.DataFrame:
    df = pd.read_parquet(INPUT_PATH)
    return df


def run_pipeline():
    print("=== TREND PIPELINE START ===")

    df = load_data()

    # агрегируем если нужно (на случай если файл не агрегирован)
    if "papers_count" not in df.columns:
        raise ValueError("Input DataFrame must contain papers_count and patents_count")

    trend_engine = TrendMetrics(df)
    enriched_df = trend_engine.compute()

    enriched_df.to_parquet(OUTPUT_PATH, index=False)

    print(f"Saved to: {OUTPUT_PATH}")
    print("=== TREND PIPELINE DONE ===")


if __name__ == "__main__":
    run_pipeline()

