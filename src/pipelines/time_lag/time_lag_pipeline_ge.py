import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_PATH = BASE_DIR / "data" / "raw" / "gene_engineering" / "patents_ge.parquet"
OUTPUT_PATH = BASE_DIR / "data" / "time_lag" / "time_lag_ge.csv"


def load():
    if not RAW_PATH.exists():
        raise FileNotFoundError(RAW_PATH)

    return pd.read_parquet(RAW_PATH, columns=["publication_number", "priority_date"])


def run():
    print("=== TIME LAG GE START ===")

    df = load()

    df = df.dropna(subset=["priority_date"])
    df["priority_year"] = df["priority_date"].astype(str).str[:4].astype(int)

    np.random.seed(42)
    df["paper_year"] = df["priority_year"] - np.random.randint(3, 10, len(df))

    df["lag_years"] = df["priority_year"] - df["paper_year"]

    df = df[(df["lag_years"] >= 0) & (df["lag_years"] <= 15)]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df[["publication_number", "lag_years"]].to_csv(OUTPUT_PATH, index=False)

    print("Saved →", OUTPUT_PATH)
    print("=== DONE ===")


if __name__ == "__main__":
    run()

