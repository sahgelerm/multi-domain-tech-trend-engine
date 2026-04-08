import pandas as pd


class TrendMetrics:
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values(["topic_name", "month"])

        df["papers_growth"] = df.groupby("topic_name")["papers_count"].pct_change()
        df["patents_growth"] = df.groupby("topic_name")["patents_count"].pct_change()

        df["trend_score"] = (
            df["papers_growth"].fillna(0) +
            df["patents_growth"].fillna(0)
        ) / 2

        return df

