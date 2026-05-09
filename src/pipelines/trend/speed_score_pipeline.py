from pathlib import Path
import pandas as pd
import numpy as np

# ==============================
# PATHS
# ==============================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_PATH = BASE_DIR / "data" / "processed" / "trend_ge.parquet"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "speed_score.csv"


# ==============================
# LOAD
# ==============================

def load_data() -> pd.DataFrame:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"trend_ge not found: {INPUT_PATH}")

    df = pd.read_parquet(INPUT_PATH)

    required = ["topic_name", "month", "papers_growth", "papers_acceleration"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"{col} missing in dataset")

    return df


# ==============================
# SPEED SCORE
# ==============================

def compute_speed_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # ==============================
    # RAW SPEED
    # ==============================

    df["speed_score_raw"] = (
        0.7 * df["papers_growth"] +
        0.3 * df["papers_acceleration"]
    )

    # ==============================
    # NORMALIZATION (per topic)
    # ==============================

    def normalize(group):
        min_val = group.min()
        max_val = group.max()
        if max_val != min_val:
            return (group - min_val) / (max_val - min_val)
        else:
            return pd.Series(0, index=group.index)

    df["speed_score"] = df.groupby("topic_name")["speed_score_raw"].transform(normalize)

    # ==============================
    # CLEAN
    # ==============================

    df = df.replace([np.inf, -np.inf], 0)
    df = df.fillna(0)

    return df


# ==============================
# SAVE
# ==============================

def save(df: pd.DataFrame):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df_out = df[
        ["topic_name", "month", "speed_score"]
    ].copy()

    df_out.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved → {OUTPUT_PATH}")


# ==============================
# PIPELINE
# ==============================

def run():
    print("=== SPEED SCORE PIPELINE START ===")

    df = load_data()
    df = compute_speed_score(df)

    save(df)

    print("=== DONE ===")


if __name__ == "__main__":
    run()
