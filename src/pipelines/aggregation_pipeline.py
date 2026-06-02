import pandas as pd
from pathlib import Path

from src.analytics.trend.metrics import TrendMetrics

# ==============================
# PATHS
# ==============================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OPENALEX_PATH = RAW_DIR / "openalex.parquet"
PATENTS_PATH = RAW_DIR / "patents.parquet"


# ==============================
# VALIDATION
# ==============================
def validate():
    if not OPENALEX_PATH.exists():
        raise FileNotFoundError(f"OpenAlex not found: {OPENALEX_PATH}")

    if not PATENTS_PATH.exists():
        raise FileNotFoundError(f"Patents not found: {PATENTS_PATH}")


# ==============================
# LOAD OPENALEX
# ==============================

def load_openalex() -> pd.DataFrame:
    df = pd.read_parquet(OPENALEX_PATH)

    required_cols = ["topic_name", "publication_date"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"{col} missing in OpenAlex")

    df["publication_date"] = pd.to_datetime(df["publication_date"], errors="co>
    df = df.dropna(subset=["publication_date", "topic_name"])
  
    df["month"] = df["publication_date"].dt.to_period("M").dt.to_timestamp()

    df = (
        df.groupby(["topic_name", "month"])
        .size()
        .reset_index(name="papers_count")
    )

    return df
# ==============================
# LOAD PATENTS
# ==============================

def load_patents() -> pd.DataFrame:
    df = pd.read_parquet(PATENTS_PATH)

    if "publication_date" not in df.columns:
        raise ValueError("publication_date missing in patents")

    df["publication_date"] = pd.to_datetime(
        df["publication_date"].astype(str),
        format="%Y%m%d",
        errors="coerce"
    )

    df = df.dropna(subset=["publication_date"])

    df["month"] = df["publication_date"].dt.to_period("M").dt.to_timestamp()

    df = (
        df.groupby("month")
        .size()
        .reset_index(name="patents_count")
    )

    return df
# ==============================
# PIPELINE
# ==============================

def run():
    print("=== TREND PIPELINE START ===")

    validate()

    papers = load_openalex()
    patents = load_patents()

    # ==============================
    # MERGE
    # ==============================

    df = pd.merge(
        papers,
        patents,
        on="month",
        how="left"
    ).copy()

    df["patents_count"] = df["patents_count"].fillna(0).astype(float)

    # ==============================
    # FIX: УБИРАЕМ ДУБЛИРОВАНИЕ
    # ==============================

    # сумма публикаций по месяцу
    df["papers_total_month"] = df.groupby("month")["papers_count"].transform(">

    # защита от деления на 0
    df["papers_share"] = df["papers_count"] / df["papers_total_month"]
    df["papers_share"] = df["papers_share"].fillna(0)

    # распределяем патенты пропорционально
    df["patents_count"] = df["patents_count"] * df["papers_share"]

    # ==============================
    # CLEAN AUX
    # ==============================

    df = df.drop(columns=["papers_total_month", "papers_share"])

    df = df.sort_values(["topic_name", "month"])
    # ==============================
    # METRICS
    # ==============================

    df = TrendMetrics(df).compute()

    # ==============================
    # CLEAN FINAL
    # ==============================

    df = df.replace([float("inf"), float("-inf")], 0)
    df = df.fillna(0)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "trend.parquet"

    df.to_parquet(output_path, index=False)

    print(f"Saved → {output_path}")
    print("=== DONE ===")

if __name__ == "__main__":
    run()
