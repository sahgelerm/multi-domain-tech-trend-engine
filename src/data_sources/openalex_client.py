"""
OpenAlex Client
================

ETL connector for retrieving scientific publications
from OpenAlex API.

Responsibilities
---------------
• Query OpenAlex Works endpoint
• Handle pagination
• Convert results to pandas DataFrame
• Basic rate-limit handling

Used in:
    Tech Trend Engine ETL pipeline
"""

import requests
import pandas as pd
import time


class OpenAlexClient:
    """
    Client for interacting with OpenAlex Works API.
    """

    BASE_URL = "https://api.openalex.org/works"

    def __init__(self, per_page: int = 200):
        """
        Parameters
        ----------
        per_page : int
            Number of results per request (max 200)
        """
        self.per_page = per_page

    def search_papers(self, keywords: list, max_pages: int = 5) -> pd.DataFrame:
        """
        Search publications by keywords.

        Parameters
        ----------
        keywords : list
            List of search keywords
        max_pages : int
            Number of pages to fetch

        Returns
        -------
        DataFrame
            Table with publications metadata
        """

        query = " ".join(keywords)

        all_results = []

        for page in range(1, max_pages + 1):

            params = {
                "search": query,
                "per_page": self.per_page,
                "page": page
            }

            response = requests.get(self.BASE_URL, params=params)

            if response.status_code != 200:
                raise RuntimeError("OpenAlex API request failed")

            data = response.json()

            results = data.get("results", [])

            if not results:
                break

            for paper in results:

                record = {
                    "id": paper.get("id"),
                    "title": paper.get("title"),
                    "publication_year": paper.get("publication_year"),
                    "publication_date": paper.get("publication_date"),
                    "cited_by_count": paper.get("cited_by_count")
                }

                all_results.append(record)

            # OpenAlex rate limit protection
            time.sleep(0.1)

        df = pd.DataFrame(all_results)

        return df
