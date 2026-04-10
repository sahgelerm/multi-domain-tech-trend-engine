import pandas as pd
import re

# ==============================
# CONFIG (GE DOMAIN)
# ==============================

CITATION_PATH = "/home/ubuntu/patents/ge/citation.parquet"
PATENTS_PATH = "/home/ubuntu/patents/ge/patents.parquet"

OUTPUT_PUB = "/home/ubuntu/time_lag_ge_publication.csv"
OUTPUT_FAMILY = "/home/ubuntu/time_lag_ge_family.csv"


# ==============================
# LOAD DATA
# ==============================

def load_data():
    print("Loading data...")

    citations = pd.read_parquet(CITATION_PATH)
    patents = pd.read_parquet(
        PATENTS_PATH,
        columns=["publication_number", "family_id", "priority_date"]
    )

    print("Citations:", len(citations))
    print("Patents:", len(patents))

    return citations, patents


# ==============================
# FILTER NPL
# ==============================

def filter_npl(citations):
    print("Filtering NPL...")

    df = citations.dropna(subset=["npl_text"]).copy()
    df["text"] = df["npl_text"]

    print("After NPL filter:", len(df))

    return df[["publication_number", "text"]]


# ==============================
# EXTRACT YEAR
# ==============================

def extract_year(text):
    if pd.isna(text):
        return None

    match = re.search(r"(19\d{2}|20\d{2})", text)

    if match:
        year = int(match.group(0))
        if 1900 <= year <= 2026:
            return year

    return None


def add_paper_year(df):
    print("Extracting paper years...")

    df["paper_year"] = df["text"].apply(extract_year)
    df = df.dropna(subset=["paper_year"])

    print("After year extraction:", len(df))

    return df


# ==============================
# PREPARE PATENTS
# ==============================

def prepare_patents(patents):
    print("Preparing patents...")

    patents = patents.dropna(subset=["priority_date"]).copy()

    patents["priority_date"] = patents["priority_date"].astype(str)
    patents["priority_year"] = patents["priority_date"].str[:4].astype(int)

    print("After priority processing:", len(patents))

    return patents[["publication_number", "family_id", "priority_year"]]


# ==============================
# MERGE
# ==============================

def merge_data(df, patents):
    print("Merging...")

    df = df.merge(
        patents,
        on="publication_number",
        how="inner"
    )

    print("After merge:", len(df))

    return df


# ==============================
# COMPUTE LAG
# ==============================

def compute_lag(df):
    print("Computing lag...")

    df["lag_years"] = df["priority_year"] - df["paper_year"]

    # ключевое улучшение
    df = df[df["paper_year"] <= df["priority_year"]]

    return df


# ==============================
# FILTER LAG
# ==============================

def filter_lag(df):
    print("Filtering lag...")

    df = df[
        (df["lag_years"] >= 0) &
        (df["lag_years"] <= 15)
    ]

    print("After lag filter:", len(df))

    return df


# ==============================
# SAVE (publication_number)
# ==============================

def save_publication(df):
    print("\n=== SAVE publication_number VERSION ===")

    df[["publication_number", "lag_years"]].to_csv(
        OUTPUT_PUB,
        index=False
    )

    print("Saved to:", OUTPUT_PUB)


# ==============================
# SAVE (family_id)
# ==============================

def save_family(df):
    print("\nAggregating by family_id...")

    family_df = (
        df.groupby("family_id")["lag_years"]
        .median()
        .reset_index()
    )

    print("Families:", len(family_df))

    print("\n=== LAG STATS (FAMILY) ===")
    print(family_df["lag_years"].describe())
    print("Median:", family_df["lag_years"].median())

    family_df.to_csv(OUTPUT_FAMILY, index=False)

    print("Saved to:", OUTPUT_FAMILY)


# ==============================
# RUN
# ==============================

def run_pipeline():
    print("=== TIME LAG GE PIPELINE START ===")

    citations, patents = load_data()

    df = filter_npl(citations)
    df = add_paper_year(df)

    patents = prepare_patents(patents)

    df = merge_data(df, patents)

    df = compute_lag(df)
    df = filter_lag(df)

    # stats
    print("\n=== LAG STATS ===")
    print(df["lag_years"].describe())
    print("Min:", df["lag_years"].min())
    print("Max:", df["lag_years"].max())
    print("Median:", df["lag_years"].median())

    # сохраняем обе версии
    save_publication(df)
    save_family(df)

    print("=== DONE ===")


if __name__ == "__main__":
    run_pipeline()
