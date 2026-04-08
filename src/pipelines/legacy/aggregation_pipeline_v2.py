import pandas as pd
from pathlib import Path


class TrendAggregationPipeline:
    """
    Lightweight aggregation pipeline:
    - NO joins
    - NO linkage
    - Memory safe
    """

    def __init__(self):
        self.openalex_path = "/home/ubuntu/OpenAlex/semiconductors_clean_signal.parquet"
        self.patents_path = "/home/ubuntu/patents/semiconductors/patents.parquet"
        self.cpc_path = "/home/ubuntu/patents/semiconductors/cpc.parquet"

        self.output_path = "data/processed/trend.parquet"

        # Semiconductor CPC filter
        self.domain_prefixes = ("H01L", "H10", "G03F")

    # -------------------------
    # OpenAlex
    # -------------------------
    def load_openalex(self):
        print("Loading OpenAlex...")

        df = pd.read_parquet(
            self.openalex_path,
            columns=["publication_date", "topic_name"]
        )

        df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce")
        df = df.dropna(subset=["publication_date"])

        df["month"] = df["publication_date"].dt.to_period("M").astype(str)

        return df

    def aggregate_papers(self, df):
        print("Aggregating papers...")

        papers = (
            df.groupby(["month", "topic_name"])
            .size()
            .reset_index(name="papers_count")
        )

        return papers

    # -------------------------
    # Patents
    # -------------------------
    def load_patents(self):
        print("Loading patents...")

        patents = pd.read_parquet(
            self.patents_path,
            columns=["publication_number", "publication_date"]
        )

        patents["publication_date"] = pd.to_datetime(
            patents["publication_date"], errors="coerce"
        )
        patents = patents.dropna(subset=["publication_date"])

        return patents

    def load_cpc(self):
        print("Loading CPC...")

        cpc = pd.read_parquet(
            self.cpc_path,
            columns=["publication_number", "code"]
        )

        return cpc

    def filter_semiconductors(self, patents, cpc):
        print("Filtering semiconductor patents...")

        cpc = cpc[cpc["code"].str.startswith(self.domain_prefixes)]

        merged = patents.merge(
            cpc[["publication_number"]],
            on="publication_number",
            how="inner"
        )

        merged["month"] = merged["publication_date"].dt.to_period("M").astype(str)

        return merged

    def aggregate_patents(self, df):
        print("Aggregating patents...")

        patents = (
            df.groupby("month")
            .size()
            .reset_index(name="patents_count")
        )

        return patents

    # -------------------------
    # Merge (SAFE)
    # -------------------------
    def combine(self, papers, patents):
        print("Combining time series...")

        df = papers.merge(
            patents,
            on="month",
            how="left"
        )

        df["patents_count"] = df["patents_count"].fillna(0)

        return df

    # -------------------------
    # Run
    # -------------------------
    def run(self):
        print("=== START TREND PIPELINE ===")

        oa = self.load_openalex()
        papers = self.aggregate_papers(oa)

        patents = self.load_patents()
        cpc = self.load_cpc()
        patents = self.filter_semiconductors(patents, cpc)
        patents = self.aggregate_patents(patents)

        df = self.combine(papers, patents)

        Path("data/processed").mkdir(parents=True, exist_ok=True)
        df.to_parquet(self.output_path, index=False)

        print("Saved:", self.output_path)
        print(df.head())

        return df


if __name__ == "__main__":
    TrendAggregationPipeline().run()

