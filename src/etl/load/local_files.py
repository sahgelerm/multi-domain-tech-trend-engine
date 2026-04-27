from pathlib import Path
import pandas as pd

# ==============================
# PATHS
# ==============================

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"

SOURCE_DIR = Path("/home/ubuntu")

OPENALEX_SOURCE = SOURCE_DIR / "OpenAlex/semiconductors_clean_signal.parquet"
PATENTS_SOURCE = SOURCE_DIR / "patents/semiconductors/patents.parquet"

OPENALEX_TARGET = RAW_DIR / "openalex.parquet"
PATENTS_TARGET = RAW_DIR / "patents.parquet"


# ==============================
# VALIDATION
# ==============================

def validate_sources():
    if not OPENALEX_SOURCE.exists():
        raise FileNotFoundError(f"Missing: {OPENALEX_SOURCE}")

    if not PATENTS_SOURCE.exists():
        raise FileNotFoundError(f"Missing: {PATENTS_SOURCE}")


# ==============================
# LOAD
# ==============================

def load_openalex():
    print("Loading OpenAlex...")
    df = pd.read_parquet(OPENALEX_SOURCE)
    print("Rows:", len(df))
    return df


def load_patents():
    print("Loading Patents...")
    df = pd.read_parquet(PATENTS_SOURCE)
    print("Rows:", len(df))
    return df


# ==============================
# SAVE
# ==============================

def save(df, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"Saved → {path}")


# ==============================
# PIPELINE
# ==============================

def run():
    print("=== ETL START ===")

    validate_sources()

    openalex = load_openalex()
    patents = load_patents()

    save(openalex, OPENALEX_TARGET)
    save(patents, PATENTS_TARGET)

    print("=== ETL DONE ===")


if __name__ == "__main__":
    run()

