from typing import List
import pandas as pd


class SemiconductorDomain:
    """
    Domain filter for semiconductor patents.
    """

    CPC_PREFIXES: List[str] = [
        "H01L",
        "H10",
        "G03F",
        "C23C",
        "H05K",
    ]

    @classmethod
    def filter_patents(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter patents by CPC codes.

        IMPORTANT:
        - assumes column 'cpc' exists
        - cpc is list or string
        """

        if "cpc" not in df.columns:
            print("WARNING: 'cpc' column not found → skipping filter")
            return df

        def match(cpc):
            if isinstance(cpc, list):
                return any(str(code).startswith(tuple(cls.CPC_PREFIXES)) for code in cpc)
            return str(cpc).startswith(tuple(cls.CPC_PREFIXES))

        return df[df["cpc"].apply(match)]


