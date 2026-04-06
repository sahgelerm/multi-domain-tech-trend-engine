import pandas as pd


class TimeSeriesBuilder:
    """
    Builds monthly time series from raw datasets.
    """

    @staticmethod
    def build_monthly_series(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """
        Convert raw data into monthly aggregated counts.

        Args:
            df: input DataFrame
            date_column: column with date

        Returns:
            DataFrame with columns:
                - month
                - count
        """

        df = df.copy()

        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")

        df = df.dropna(subset=[date_column])

        df["month"] = df[date_column].dt.to_period("M").dt.to_timestamp()

        result = (
            df.groupby("month")
            .size()
            .reset_index(name="count")
            .sort_values("month")
        )

        return result

