import pandas as pd
from pathlib import Path

# ==============================
# PATHS
# ==============================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"

OPENALEX_PATH = RAW_DIR / "openalex.parquet"
PATENTS_PATH = RAW_DIR / "patents.parquet"


# ==============================
# VALIDATION
# ==============================

def validate():
    if not OPENALEX_PATH.exists():
        raise FileNotFoundError(f"Missing: {OPENALEX_PATH}")

    if not PATENTS_PATH.exists():
        raise FileNotFoundError(f"Missing: {PATENTS_PATH}")


# ==============================
# LOAD
# ==============================

def load_data():
    validate()

    print("Loading data...")

    openalex = pd.read_parquet(OPENALEX_PATH)
    patents = pd.read_parquet(PATENTS_PATH)

    print("OpenAlex:", len(openalex))
    print("Patents:", len(patents))

    return openalex, patents


# ==============================
# INSPECTION
# ==============================

def inspect_openalex(df):
    print("\nOPENALEX")

    print("Columns:", df.columns.tolist())
    print("Missing publication_date:", df["publication_date"].isna().sum())
    print("Topics:", df["topic_name"].nunique())


def inspect_patents(df):
    print("\nPATENTS")

    df["publication_date"] = pd.to_datetime(
        df["publication_date"].astype(str),
        format="%Y%m%d",
        errors="coerce"
    )

    print("Min date:", df["publication_date"].min())
    print("Max date:", df["publication_date"].max())


# ==============================
# RUN
# ==============================

def run():
    print("=== DEBUG START ===")

    openalex, patents = load_data()

    inspect_openalex(openalex)
    inspect_patents(patents)

    print("=== DEBUG DONE ===")


if __name__ == "__main__":
    run()

