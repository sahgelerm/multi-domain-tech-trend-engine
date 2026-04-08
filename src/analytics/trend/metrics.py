import pandas as pd
import numpy as np


class TrendMetrics:
    """
    Compute trend-related metrics on top of time series data.

    Expected input schema:
    month | topic_name | papers_count | patents_count
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def _prepare(self) -> pd.DataFrame:
        df = self.df.copy()

        df["month"] = pd.to_datetime(df["month"])
        df = df.sort_values(["topic_name", "month"])

        return df

    def _compute_growth(self, series: pd.Series, window: int) -> float:
        """
        CAGR-like growth over a rolling window.
        """
        if len(series) < window:
            return 0.0

        start = series.iloc[-window]
        end = series.iloc[-1]

        if start <= 0:
            return 0.0

        return (end / start) ** (1 / window) - 1

    def _compute_acceleration(self, series: pd.Series, window: int) -> float:
        """
        Acceleration = growth(current window) - growth(previous window)
        """
        if len(series) < window * 2:
            return 0.0

        current_growth = self._compute_growth(series.iloc[-window:], window)
        prev_growth = self._compute_growth(series.iloc[-2 * window:-window], window)

        return current_growth - prev_growth

    def _label_trend(self, score: float) -> str:
        if score >= 0.7:
            return "Emerging"
        elif score >= 0.4:
            return "Growing"
        elif score >= 0.2:
            return "Stable"
        else:
            return "Cooling"

    def compute(self) -> pd.DataFrame:
        df = self._prepare()

        results = []

        for topic, group in df.groupby("topic_name"):
            group = group.sort_values("month")

            papers = group["papers_count"]
            patents = group["patents_count"]

            papers_growth = self._compute_growth(papers, window=3)
            patents_growth = self._compute_growth(patents, window=3)

            papers_acc = self._compute_acceleration(papers, window=3)
            patents_acc = self._compute_acceleration(patents, window=3)

            combined_growth = (papers_growth + patents_growth) / 2

            # Trend score (simple weighted heuristic MVP)
            trend_score = (
                0.5 * papers_growth +
                0.5 * patents_growth +
                0.2 * papers_acc +
                0.2 * patents_acc
            )

            trend_score = float(np.clip(trend_score, 0, 1))

            results.append({
                "topic_name": topic,
                "papers_growth": papers_growth,
                "patents_growth": patents_growth,
                "papers_acceleration": papers_acc,
                "patents_acceleration": patents_acc,
                "combined_growth": combined_growth,
                "trend_score": trend_score,
                "trend_label": self._label_trend(trend_score)
            })

        metrics_df = pd.DataFrame(results)

        return df.merge(metrics_df, on="topic_name", how="left")

