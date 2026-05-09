from pathlib import Path
import pandas as pd

# ==============================
# PATHS
# ==============================

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw" / "gene_engineering"

SOURCE_DIR = Path("/home/ubuntu")

OPENALEX_SOURCE = SOURCE_DIR / "OpenAlex/gene_engineering_clean_signal.parquet"
PATENTS_SOURCE = SOURCE_DIR / "patents/ge/patents.parquet"

OPENALEX_TARGET = RAW_DIR / "openalex_ge.parquet"
PATENTS_TARGET = RAW_DIR / "patents_ge.parquet"


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
    print("Loading OpenAlex (GE)...")
    df = pd.read_parquet(OPENALEX_SOURCE)
    print("Rows:", len(df))
    return df


def load_patents():
    print("Loading Patents (GE)...")
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
    print("=== ETL GE START ===")

    validate_sources()

    openalex = load_openalex()
    patents = load_patents()

    save(openalex, OPENALEX_TARGET)
    save(patents, PATENTS_TARGET)

    print("=== ETL GE DONE ===")


if __name__ == "__main__":
    run()
