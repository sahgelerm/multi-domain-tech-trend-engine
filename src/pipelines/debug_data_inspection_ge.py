import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "src" / "data" / "raw" / "gene_engineering"

OPENALEX_PATH = RAW_DIR / "openalex_ge.parquet"
PATENTS_PATH = RAW_DIR / "patents_ge.parquet"


def validate():
    if not OPENALEX_PATH.exists():
        raise FileNotFoundError(f"Missing: {OPENALEX_PATH}")

    if not PATENTS_PATH.exists():
        raise FileNotFoundError(f"Missing: {PATENTS_PATH}")


def run():
    print("=== DEBUG GE START ===")

    validate()

    openalex = pd.read_parquet(OPENALEX_PATH)
    patents = pd.read_parquet(PATENTS_PATH)

    print("OpenAlex:", len(openalex))
    print("Patents:", len(patents))

    print("Topics:", openalex["topic_name"].nunique())

    print("=== DEBUG GE DONE ===")


if __name__ == "__main__":
    run()

