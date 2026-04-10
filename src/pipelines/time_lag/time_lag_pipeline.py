import pandas as pd
import re

def load_data():
    print("Loading data...")

    citations = pd.read_parquet(
        "/home/ubuntu/patents/semiconductors/citation.parquet"
    )

    patents = pd.read_parquet(
        "/home/ubuntu/patents/semiconductors/patents.parquet",
        columns=["publication_number", "priority_date"]
    )

    print("Citations:", len(citations))
    print("Patents:", len(patents))

    return citations, patents

def filter_npl(citations):
    print("Filtering NPL...")

    df = citations.dropna(subset=["npl_text"]).copy()
    df["text"] = df["npl_text"]

    print("After NPL filter:", len(df))

    return df[["publication_number", "text"]]

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

def prepare_patents(patents):
    print("Preparing patents...")

    patents = patents.dropna(subset=["priority_date"]).copy()

    patents["priority_date"] = patents["priority_date"].astype(str)
    patents["priority_year"] = patents["priority_date"].str[:4].astype(int)

    print("After priority processing:", len(patents))

    return patents[["publication_number", "priority_year"]]

def merge_data(df, patents):
    print("Merging...")

    df = df.merge(
        patents,
        on="publication_number",
        how="inner"
    )

    print("After merge:", len(df))

    return df

def compute_lag(df):
    print("Computing lag...")

    df["lag_years"] = df["priority_year"] - df["paper_year"]

    return df

def filter_lag(df):
    print("Filtering lag...")

    # КРИТИЧЕСКОЕ улучшение
    df = df[df["paper_year"] <= df["priority_year"]]

    df = df[
        (df["lag_years"] >= 0) &
        (df["lag_years"] <= 15)
    ]

    print("After lag filter:", len(df))

    return df

def compute_stats(df):
    print("\n=== LAG STATS ===")

    print(df["lag_years"].describe())
    print("Min:", df["lag_years"].min())
    print("Max:", df["lag_years"].max())
    print("Median:", df["lag_years"].median())

def save_results(df):
    path = "/home/ubuntu/time_lag_results.csv"

    df[["publication_number", "lag_years"]].to_csv(
        path,
        index=False
    )

    print("Saved to:", path)

def run():
    print("=== TIME LAG PIPELINE START ===")

    citations, patents = load_data()

    df = filter_npl(citations)
    df = add_paper_year(df)

    patents = prepare_patents(patents)

    df = merge_data(df, patents)
    df = compute_lag(df)
    df = filter_lag(df)

    compute_stats(df)
    save_results(df)

    print("=== DONE ===")

if __name__ == "__main__":
    run()


