import pandas as pd
import numpy as np


class TrendMetrics:
    """
    Расчет трендовых метрик по временным рядам.

    Вход:
        topic_name | month | papers_count | patents_count

    Выход:
        + papers_growth
        + patents_growth
        + acceleration
        + trend_score
        + trend_label
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def _prepare(self) -> pd.DataFrame:
        df = self.df.copy()

        df["month"] = pd.to_datetime(df["month"], errors="coerce")
        df = df.dropna(subset=["month"])

        df = df.sort_values(["topic_name", "month"])

        df["papers_count"] = df["papers_count"].fillna(0)
        df["patents_count"] = df["patents_count"].fillna(0)

        return df

    @staticmethod
    def _safe_pct_change(series: pd.Series) -> pd.Series:
        prev = series.shift(1)
        growth = (series - prev) / prev.replace(0, np.nan)
        return growth.replace([np.inf, -np.inf], 0).fillna(0)

    def compute(self) -> pd.DataFrame:
        df = self._prepare()

        # ==============================
        # GROWTH
        # ==============================

        df["papers_growth"] = df.groupby("topic_name")["papers_count"].transform(
            self._safe_pct_change
        )

        df["patents_growth"] = df.groupby("topic_name")["patents_count"].transform(
            self._safe_pct_change
        )

        # ==============================
        # SMOOTHING
        # ==============================

        df["papers_growth"] = df.groupby("topic_name")["papers_growth"].transform(
            lambda x: x.rolling(window=3, min_periods=1).mean()
        )

        df["patents_growth"] = df.groupby("topic_name")["patents_growth"].transform(
            lambda x: x.rolling(window=3, min_periods=1).mean()
        )

        # ==============================
        # ACCELERATION
        # ==============================

        df["papers_acceleration"] = df.groupby("topic_name")["papers_growth"].diff().fillna(0)
        df["patents_acceleration"] = df.groupby("topic_name")["patents_growth"].diff().fillna(0)

        # ==============================
        # TREND SCORE
        # ==============================

        df["trend_score_raw"] = (
            0.4 * df["papers_growth"]
            + 0.4 * df["patents_growth"]
            + 0.1 * df["papers_acceleration"]
            + 0.1 * df["patents_acceleration"]
        )

        # ✅ FIX: нормализация ПО КАЖДОЙ ТЕМЕ
        def normalize(group):
            min_val = group.min()
            max_val = group.max()
            if max_val != min_val:
                return (group - min_val) / (max_val - min_val)
            else:
                return pd.Series(0, index=group.index)

        df["trend_score"] = df.groupby("topic_name")["trend_score_raw"].transform(normalize)

        # ==============================
        # LABEL
        # ==============================

        def label(score: float) -> str:
            if score >= 0.7:
                return "Зарождающийся"
            elif score >= 0.4:
                return "Растущий"
            elif score >= 0.2:
                return "Стабильный"
            else:
                return "Снижающийся"

        df["trend_label"] = df["trend_score"].apply(label)

        # ==============================
        # FINAL CLEAN
        # ==============================

        df = df.replace([np.inf, -np.inf], 0)
        df = df.fillna(0)

        return df

