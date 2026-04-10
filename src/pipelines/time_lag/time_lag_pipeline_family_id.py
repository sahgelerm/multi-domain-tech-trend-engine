import pandas as pd
import re


# =========================
# LOAD DATA
# =========================
def load_data():
    print("Loading data...")

    citations = pd.read_parquet(
        "/home/ubuntu/patents/semiconductors/citation.parquet"
    )

    patents = pd.read_parquet(
        "/home/ubuntu/patents/semiconductors/patents.parquet",
        columns=["publication_number", "priority_date", "family_id"]
    )

    print("Citations:", len(citations))
    print("Patents:", len(patents))

    return citations, patents


# =========================
# FILTER NPL
# =========================
def filter_npl(citations):
    print("Filtering NPL...")

    df = citations.dropna(subset=["npl_text"]).copy()
    df["text"] = df["npl_text"]

    print("After NPL filter:", len(df))

    return df[["publication_number", "text"]]


# =========================
# EXTRACT YEAR
# =========================
def extract_year(text):
    if pd.isna(text):
        return None

    match = re.search(r"(19\d{2}|20\d{2})", text)

    if match:
        year = int(match.group(0))
        if 1900 <= year <= 2026:
            return year

    return None


def extract_paper_years(df):
    print("Extracting paper years...")

    df["paper_year"] = df["text"].apply(extract_year)
    df = df.dropna(subset=["paper_year"])

    print("After year extraction:", len(df))

    return df


# =========================
# PREPARE PATENTS
# =========================
def prepare_patents(patents):
    print("Preparing patents...")

    patents = patents.dropna(subset=["priority_date", "family_id"]).copy()

    patents["priority_date"] = patents["priority_date"].astype(str)
    patents["priority_year"] = patents["priority_date"].str[:4].astype(int)

    print("After priority processing:", len(patents))

    return patents[["publication_number", "priority_year", "family_id"]]


# =========================
# MERGE
# =========================
def merge_data(df, patents):
    print("Merging...")

    df = df.merge(
        patents,
        on="publication_number",
        how="inner"
    )

    print("After merge:", len(df))

    return df


# =========================
# COMPUTE LAG
# =========================
def compute_lag(df):
    print("Computing lag...")

    df["lag_years"] = df["priority_year"] - df["paper_year"]

    return df


# =========================
# FILTER LAG
# =========================
def filter_lag(df):
    print("Filtering lag...")

    df = df[
        (df["lag_years"] >= 0) &
        (df["lag_years"] <= 15)
    ]

    # 🔥 ВАЖНОЕ УЛУЧШЕНИЕ
    df = df[df["paper_year"] <= df["priority_year"]]

    print("After lag filter:", len(df))

    return df


# =========================
# AGGREGATE BY FAMILY
# =========================
def aggregate_family(df):
    print("Aggregating by family_id...")

    family_df = (
        df.groupby("family_id")["lag_years"]
        .median()
        .reset_index()
    )

    print("Families:", len(family_df))

    return family_df


# =========================
# SAVE
# =========================
def save_results(df):
    output_path = "/home/ubuntu/time_lag_family.csv"

    df.to_csv(output_path, index=False)

    print(f"Saved to: {output_path}")


# =========================
# MAIN PIPELINE
# =========================
def run_pipeline():
    print("=== TIME LAG PIPELINE START ===")

    citations, patents = load_data()

    df = filter_npl(citations)
    df = extract_paper_years(df)

    patents = prepare_patents(patents)

    df = merge_data(df, patents)

    df = compute_lag(df)
    df = filter_lag(df)

    # Улучшение
    family_df = aggregate_family(df)

    print("\n=== LAG STATS (FAMILY) ===")
    print(family_df["lag_years"].describe())
    print("Median:", family_df["lag_years"].median())

    save_results(family_df)

    print("=== DONE ===")


if __name__ == "__main__":
    run_pipeline()

