"""
data_loader.py - загрузка данных для дашборда
Режимы работы:
- bigquery: прямое подключение к BigQuery (production)
- parquet: локальные файлы (для тестирования)
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from pathlib import Path
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
# Режим работы (можно переключить через переменную окружения)
MODE = os.getenv('DASHBOARD_MODE', 'bigquery')  # 'bigquery' или 'parquet'

# Пути (для parquet-режима)
PROJECT_ROOT = Path(__file__).parent.parent
SUMMARY_DIR = PROJECT_ROOT / "data" / "summary"

# BigQuery настройки - ВАШ PROJECT_ID
BIGQUERY_PROJECT = os.getenv('GCP_PROJECT', 'project-7a7c09b1-b387-4931-856')
BIGQUERY_DATASET = os.getenv('GCP_DATASET', 'tech_trends')  # УТОЧНИТЬ У НАТАЛЬИ!
BIGQUERY_KEY_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/home/ubuntu/.gcp/service-key.json')

# Пути к JSON-метрикам от коллег (на сервере)
METRICS_PATH = Path('/home/ubuntu/indlab-data/metrics')
CLUSTERS_PATH = Path('/home/ubuntu/indlab-data/clusters')

# Маппинг доменов
DOMAIN_MAP = {
    "Полупроводники": "semiconductors",
    "Генная инженерия": "gene_engineering"
}

# ========== BIGQUERY КЛИЕНТ ==========
def get_bigquery_client():
    """Инициализация клиента BigQuery"""
    try:
        # Пробуем использовать service account ключ
        if os.path.exists(BIGQUERY_KEY_PATH):
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_file(
                BIGQUERY_KEY_PATH
            )
            from google.cloud import bigquery
            client = bigquery.Client(
                project=BIGQUERY_PROJECT,
                credentials=credentials
            )
            logger.info(f"✅ BigQuery клиент инициализирован (проект: {client.project})")
            return client
        else:
            # Пробуем стандартную аутентификацию (если запущено на GCP)
            from google.cloud import bigquery
            client = bigquery.Client(project=BIGQUERY_PROJECT)
            logger.info(f"✅ BigQuery клиент инициализирован через ADC")
            return client
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к BigQuery: {e}")
        return None

# ========== ЗАГРУЗКА ДАННЫХ ИЗ BIGQUERY ==========
@st.cache_data(ttl=3600)  # кэш на 1 час
def load_from_bigquery(domain_key):
    """
    Загрузка данных из BigQuery для указанного домена.
    Возвращает: dates, papers, patents, metrics
    """
    client = get_bigquery_client()
    if client is None:
        logger.warning("BigQuery недоступен, переключаюсь на parquet-режим")
        return load_from_parquet(domain_key)
    
    # 1. Загружаем временные ряды
    query_timeseries = f"""
    SELECT 
        DATE_TRUNC(publication_date, MONTH) as month,
        COUNTIF(type = 'publication') as papers_count,
        COUNTIF(type = 'patent') as patents_count
    FROM `{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.publications`
    WHERE domain = '{domain_key}'
      AND publication_date >= '2015-01-01'
    GROUP BY month
    ORDER BY month
    """
    
    try:
        df_ts = client.query(query_timeseries).to_dataframe()
        
        if len(df_ts) == 0:
            logger.warning(f"Нет данных для {domain_key} в BigQuery")
            return load_from_parquet(domain_key)
        
        dates = df_ts['month'].dt.strftime('%Y-%m').tolist()
        papers = df_ts['papers_count'].tolist()
        patents = df_ts['patents_count'].tolist()
        
        logger.info(f"✅ Загружено {len(dates)} месяцев из BigQuery")
        
    except Exception as e:
        logger.error(f"❌ Ошибка запроса временных рядов: {e}")
        return load_from_parquet(domain_key)
    
    # 2. Загружаем агрегированные метрики
    query_metrics = f"""
    SELECT 
        COUNTIF(type = 'publication') as papers_total,
        COUNTIF(type = 'patent') as patents_total,
        AVG(CASE WHEN type = 'publication' THEN cited_by_count END) as papers_cited_avg
    FROM `{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.publications`
    WHERE domain = '{domain_key}'
    """
    
    try:
        df_metrics = client.query(query_metrics).to_dataframe()
        row = df_metrics.iloc[0] if len(df_metrics) > 0 else {'papers_total': 0, 'patents_total': 0, 'papers_cited_avg': 0}
        
        # 3. Загружаем топ-заявителей (для патентов)
        query_assignees = f"""
        SELECT assignee, COUNT(*) as cnt
        FROM `{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.publications`
        WHERE domain = '{domain_key}'
          AND type = 'patent'
          AND assignee IS NOT NULL
        GROUP BY assignee
        ORDER BY cnt DESC
        LIMIT 5
        """
        df_assignees = client.query(query_assignees).to_dataframe()
        
        top_assignees = df_assignees['assignee'].tolist() if len(df_assignees) > 0 else ['Нет данных']
        assignee_values = df_assignees['cnt'].tolist() if len(df_assignees) > 0 else [0]
        
        # 4. География (на основе country_code)
        query_geo = f"""
        SELECT country_code, COUNT(*) as cnt
        FROM `{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.publications`
        WHERE domain = '{domain_key}'
          AND type = 'patent'
          AND country_code IS NOT NULL
        GROUP BY country_code
        ORDER BY cnt DESC
        LIMIT 5
        """
        df_geo = client.query(query_geo).to_dataframe()
        
        # Маппинг кодов стран в названия
        country_names = {
            'US': 'США', 'CN': 'Китай', 'JP': 'Япония', 'KR': 'Южная Корея',
            'EP': 'Европа', 'WO': 'Мир', 'DE': 'Германия', 'FR': 'Франция',
            'GB': 'Великобритания', 'CA': 'Канада'
        }
        countries = [country_names.get(code, code) for code in df_geo['country_code'].tolist()] if len(df_geo) > 0 else ['Нет данных']
        country_values = df_geo['cnt'].tolist() if len(df_geo) > 0 else [100]
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки метрик: {e}")
        row = {'papers_total': 0, 'patents_total': 0, 'papers_cited_avg': 0}
        top_assignees = ['Нет данных']
        assignee_values = [0]
        countries = ['Нет данных']
        country_values = [100]
    
    # 5. Загружаем метрики от Сергея и Марии (из JSON)
    speed_score = load_speed_score(domain_key)
    trend_score_data = load_trend_score(domain_key)
    
    # Формируем метрики
    metrics = {
        'papers_total': int(row.get('papers_total', 0)),
        'patents_total': int(row.get('patents_total', 0)),
        'papers_cited_avg': round(float(row.get('papers_cited_avg', 0)), 1),
        'papers_growth': calculate_growth(papers, 12),  # годовой рост
        'patents_growth': calculate_growth(patents, 12),
        'time_lag': speed_score.get('median_lag', 7.0),
        'time_lag_change': speed_score.get('lag_change', '0'),
        'trend_score': trend_score_data.get('trend_score', 78),
        'trend_status': trend_score_data.get('status', 'Growing'),
        'ai_share': load_ai_share(domain_key, client),
        'top_assignees': top_assignees,
        'assignee_values': assignee_values,
        'countries': countries,
        'country_values': country_values,
        'speed_score': speed_score.get('speed_score', 0),
        'lag_distribution': speed_score.get('distribution', {})
    }
    
    return np.array(dates), np.array(papers), np.array(patents), metrics

# ========== ЗАГРУЗКА МЕТРИК ОТ КОЛЛЕГ ==========
@st.cache_data(ttl=3600)
def load_speed_score(domain_key):
    """Загрузка Speed Score от Сергея"""
    json_path = METRICS_PATH / f"{domain_key}_speed_score.json"
    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except:
            pass
    # Значения по умолчанию (из результатов Сергея)
    return {
        'speed_score': 0.059 if domain_key == 'semiconductors' else 0.091,
        'median_lag': 7.0 if domain_key == 'semiconductors' else 4.0,
        'lag_change': '-0.3',
        'distribution': {'fast': 0.15, 'normal': 0.35, 'slow': 0.35, 'very_slow': 0.15}
    }

@st.cache_data(ttl=3600)
def load_trend_score(domain_key):
    """Загрузка Trend Score от Марии"""
    json_path = METRICS_PATH / f"{domain_key}_trend_score.json"
    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'trend_score': 78,
        'status': 'Growing',
        'confidence': 0.85
    }

@st.cache_data(ttl=3600)
def load_ai_share(domain_key, client=None):
    """Загрузка доли AI-патентов (G06N*)"""
    if client:
        query = f"""
        SELECT COUNT(DISTINCT publication_number) as ai_count
        FROM `{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.publications`
        WHERE domain = '{domain_key}'
          AND type = 'patent'
          AND cpc_code LIKE 'G06N%'
        """
        try:
            df = client.query(query).to_dataframe()
            if len(df) > 0:
                total = metrics_cache.get('patents_total', 0) if 'metrics_cache' in dir() else 0
                if total > 0:
                    return int(df['ai_count'].iloc[0] / total * 100)
        except:
            pass
    return 35  # дефолтное значение

def calculate_growth(series, months):
    """Расчет годового роста"""
    if len(series) >= months:
        current = series[-1]
        previous = series[-months-1] if len(series) > months else series[0]
        if previous > 0:
            return round((current - previous) / previous * 100, 1)
    return 15  # дефолтное значение

# ========== ЗАГРУЗКА ИЗ PARQUET (РЕЗЕРВ) ==========
@st.cache_data(ttl=3600)
def load_from_parquet(domain_key):
    """Загрузка данных из Parquet-файлов (резервный режим)"""
    summary_file = SUMMARY_DIR / f"{domain_key}_summary.parquet"
    
    if summary_file.exists():
        df = pd.read_parquet(summary_file)
        row = df.iloc[0]
        
        dates = row.get('dates', [])
        papers = row.get('papers', [])
        patents = row.get('patents', [0] * len(dates)) if 'patents' in row else [0] * len(dates)
        
        metrics = {
            'papers_total': int(row.get('papers_total', 0)),
            'patents_total': int(row.get('patents_total', 0)),
            'papers_cited_avg': float(row.get('papers_cited_avg', 0)),
            'papers_growth': float(row.get('papers_growth', 15)),
            'patents_growth': float(row.get('patents_growth', 22)),
            'time_lag': float(row.get('time_lag', 2.5)),
            'time_lag_change': row.get('time_lag_change', '-0.3'),
            'trend_score': int(row.get('trend_score', 78)),
            'trend_status': row.get('trend_status', 'Растущий'),
            'ai_share': int(row.get('ai_share', 35)),
            'top_assignees': row.get('top_assignees', ['Нет данных']),
            'assignee_values': row.get('assignee_values', [0]),
            'countries': row.get('countries', ['Нет данных']),
            'country_values': row.get('country_values', [100])
        }
        
        logger.info(f"✅ Данные загружены из Parquet: {summary_file}")
        return np.array(dates), np.array(papers), np.array(patents), metrics
    
    # Если нет summary, генерируем тестовые
    logger.warning(f"⚠️ Parquet файл не найден: {summary_file}, генерирую тестовые данные")
    return generate_fallback_data(domain_key)

def generate_fallback_data(domain_key):
    """Генерация тестовых данных (если ничего нет)"""
    dates = pd.date_range(start='2020-01-01', end='2025-12-01', freq='MS').strftime('%Y-%m').tolist()
    papers = np.random.poisson(lam=50, size=len(dates)).cumsum()
    patents = np.random.poisson(lam=30, size=len(dates)).cumsum()
    
    metrics = {
        'papers_total': int(papers[-1]),
        'patents_total': int(patents[-1]),
        'papers_cited_avg': round(np.random.uniform(10, 25), 1),
        'papers_growth': round(np.random.uniform(5, 15), 1),
        'patents_growth': round(np.random.uniform(8, 20), 1),
        'time_lag': round(np.random.uniform(2.5, 4.5), 1),
        'time_lag_change': f"+{round(np.random.uniform(0.1, 0.5), 1)}",
        'trend_score': np.random.randint(60, 95),
        'trend_status': np.random.choice(['Взрывной рост', 'Стабильный рост', 'Созревание']),
        'ai_share': np.random.randint(15, 45),
        'top_assignees': ['Тест-Компания А', 'Тест-Компания Б', 'Тест-Компания В'],
        'assignee_values': [150, 90, 45],
        'countries': ['США', 'Китай', 'Германия'],
        'country_values': [48, 32, 20]
    }
    
    return np.array(dates), np.array(papers), np.array(patents), metrics

# ========== ЗАГРУЗКА КЛАСТЕРОВ (ПОДТЕХНОЛОГИИ) ==========
@st.cache_data(ttl=3600)
def load_clusters(domain_key):
    """Загрузка кластеров от Дениса для подтехнологий"""
    clusters_file = CLUSTERS_PATH / f"{domain_key}_clusters.parquet"
    if clusters_file.exists():
        try:
            df = pd.read_parquet(clusters_file)
            return df
        except Exception as e:
            logger.error(f"Ошибка загрузки кластеров: {e}")
    
    # Возвращаем тестовые данные
    if domain_key == 'semiconductors':
        return pd.DataFrame({
            'cluster_name': ['FinFET/GAA', 'EUV литография', 'Advanced Packaging', 'GaN/SiC', 'MRAM память'],
            'growth': [45, 38, 32, 28, 25],
            'documents_count': [1250, 890, 650, 420, 380]
        })
    else:
        return pd.DataFrame({
            'cluster_name': ['CRISPR-Cas9', 'CRISPR-Cas12/13', 'Вирусные векторы', 'Липидные наночастицы', 'CAR-T'],
            'growth': [52, 48, 41, 38, 35],
            'documents_count': [890, 650, 480, 320, 280]
        })

# ========== ОСНОВНЫЕ ФУНКЦИИ ДЛЯ ДАШБОРДА ==========
def load_domain_data(domain_name):
    """
    Главная функция загрузки данных для дашборда.
    Использует режим, заданный в MODE.
    """
    domain_key = DOMAIN_MAP.get(domain_name, domain_name.lower())
    
    logger.info(f"Загрузка данных для {domain_name} (режим: {MODE})")
    
    if MODE == 'bigquery':
        return load_from_bigquery(domain_key)
    else:
        return load_from_parquet(domain_key)

def get_clusters_for_domain(domain_name):
    """Получение данных о кластерах для домена"""
    domain_key = DOMAIN_MAP.get(domain_name, domain_name.lower())
    return load_clusters(domain_key)

# ========== ИНИЦИАЛИЗАЦИЯ ПРИ ЗАПУСКЕ ==========
logger.info(f"🚀 data_loader инициализирован. Режим: {MODE}")
logger.info(f"   BigQuery проект: {BIGQUERY_PROJECT}")
if MODE == 'bigquery':
    logger.info(f"   Путь к ключу: {BIGQUERY_KEY_PATH if os.path.exists(BIGQUERY_KEY_PATH) else 'не найден'}")
