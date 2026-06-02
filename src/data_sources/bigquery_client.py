"""
patents_client.py

ETL клиент для загрузки патентных данных из Google Patents Public Dataset (BigQuery).

Источник:
patents-public-data.patents.publications

Модуль отвечает за:
- подключение к BigQuery
- выполнение SQL-запросов
- фильтрацию по CPC кодам домена
- возврат данных в формате pandas DataFrame
"""

from google.cloud import bigquery
import pandas as pd
from typing import List
from tqdm import tqdm


class PatentsClient:
    """
    Клиент для работы с Google Patents BigQuery Dataset.

    Responsibilities:
    ----------------
    - создание соединения с BigQuery
    - выполнение SQL-запросов
    - загрузка результатов в pandas DataFrame
    """

    def __init__(self, project_id: str):
        """
        Инициализация клиента.

        Parameters
        ----------
        project_id : str
            ID проекта Google Cloud
        """

        self.project_id = project_id

        # создание клиента BigQuery
        self.client = bigquery.Client(project=project_id)

    def build_cpc_filter(self, cpc_prefixes: List[str]) -> str:
        """
        Генерация SQL фильтра для CPC кодов.

        Parameters
        ----------
        cpc_prefixes : List[str]
            список префиксов CPC кодов

        Example
        -------
        ["H01L", "H10", "G03F"]

        Returns
        -------
        str
            SQL условие фильтрации
        """

        filters = []

        for prefix in cpc_prefixes:
            filters.append(f"STARTS_WITH(cpc.code, '{prefix}')")

        return " OR ".join(filters)

    def fetch_patents(
        self,
        cpc_prefixes: List[str],
        start_date: str = "2015-01-01",
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Загрузка патентов по CPC кодам.

        Parameters
        ----------
        cpc_prefixes : List[str]
            CPC коды домена

        start_date : str
            минимальная дата публикации

        limit : int
            ограничение количества строк

        Returns
        -------
        pd.DataFrame
        """

        cpc_filter = self.build_cpc_filter(cpc_prefixes)

        query = f"""
        SELECT
            publication_number,
            publication_date,
            country_code,
            assignee_harmonized,
            title_localized
        FROM
            `patents-public-data.patents.publications`,
            UNNEST(cpc) as cpc
        WHERE
            ({cpc_filter})
            AND publication_date >= '{start_date}'
        LIMIT {limit}
        """

        print("Executing BigQuery query...")

        query_job = self.client.query(query)

        df = query_job.to_dataframe()

        return df
