import pandas as pd

class TimeSeriesBuilder:
    """
    Построение временных рядов (месячных) из сырых данных.
    """
    @staticmethod
    def build_monthly_series(
        df: pd.DataFrame,
        date_column: str,
        topic_column: str = None
    ) -> pd.DataFrame:
        """
        Преобразует данные в monthly time series.

        Args:
            df: входной DataFrame
            date_column: колонка с датой
            topic_column: колонка с темой (опционально)

        Returns:
            DataFrame:
                topic_name | month | count
        """

        df = df.copy()

        # ==============================
        # DATE
        # ==============================

        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
        df = df.dropna(subset=[date_column])

        df["month"] = df[date_column].dt.to_period("M").dt.to_timestamp()

        # ==============================
        # GROUPING
        # ==============================

        if topic_column and topic_column in df.columns:
            result = (
                df.groupby([topic_column, "month"])
                .size()
                .reset_index(name="count")
                .rename(columns={topic_column: "topic_name"})
            )
        else:
            result = (
                df.groupby("month")
                .size()
                .reset_index(name="count")
            )
            result["topic_name"] = "global"

        result = result.sort_values(["topic_name", "month"])

        return result
