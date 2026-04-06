"""
Aggregation Pipeline

Builds:
- papers time series
- patents time series

Run:
    python -m src.pipelines.aggregation_pipeline
"""

import os
import pandas as pd

from src.analytics.aggregations.time_series import TimeSeriesBuilder
from src.domains.semiconductors import SemiconductorDomain


# ===== PATHS =====
OPENALEX_PATH = "/home/ubuntu/OpenAlex/semiconductors_clean_full.parquet"
PATENTS_DIR = "/home/ubuntu/patents/semiconductors"

OUTPUT_DIR = "/home/ubuntu/indlab-data/processed"


class AggregationPipeline:
    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    # -------------------------
    # LOAD PAPERS
    # -------------------------
    def load_papers(self) -> pd.DataFrame:
        print(f"Loading OpenAlex from {OPENALEX_PATH}")

        df = pd.read_parquet(OPENALEX_PATH)

        print(f"Papers loaded: {df.shape}")

        return df

    # -------------------------
    # LOAD PATENTS (robust)
    # -------------------------
    def load_patents(self) -> pd.DataFrame:
        print(f"Loading patents from {PATENTS_DIR}")

        files = [
            f for f in os.listdir(PATENTS_DIR)
            if f.endswith(".parquet")
        ]

        if not files:
            raise ValueError("No parquet files found in patents directory")

        dfs = []

        for f in files:
            path = os.path.join(PATENTS_DIR, f)
            print(f"Reading {path}")

            df_part = pd.read_parquet(path)
            dfs.append(df_part)

        df = pd.concat(dfs, ignore_index=True)

        print(f"Patents loaded: {df.shape}")

        return df

    # -------------------------
    # MAIN PIPELINE
    # -------------------------
    def run(self):
        print("=== START AGGREGATION PIPELINE ===")

        # ---- Load ----
        papers = self.load_papers()
        patents = self.load_patents()

        # ---- Validate columns ----
        if "publication_date" not in papers.columns:
            raise ValueError("OpenAlex missing 'publication_date'")

        if "publication_date" not in patents.columns:
            print("WARNING: patents missing 'publication_date'")
            print("Available columns:", patents.columns)

        # ---- Filter patents ----
        patents_filtered = SemiconductorDomain.filter_patents(patents)

        print(f"Patents after filter: {len(patents_filtered)}")

        # ---- Time series ----
        papers_ts = TimeSeriesBuilder.build_monthly_series(
            papers,
            "publication_date"
        )

        patents_ts = TimeSeriesBuilder.build_monthly_series(
            patents_filtered,
            "publication_date"
        )

        # ---- Save ----
        papers_out = os.path.join(OUTPUT_DIR, "papers_ts.csv")
        patents_out = os.path.join(OUTPUT_DIR, "patents_ts.csv")

        papers_ts.to_csv(papers_out, index=False)
        patents_ts.to_csv(patents_out, index=False)

        print("Saved:")
        print(papers_out)
        print(patents_out)

        print("=== DONE ===")


if __name__ == "__main__":
    pipeline = AggregationPipeline()
    pipeline.run()

