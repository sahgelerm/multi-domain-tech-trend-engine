# Multi-Domain Dashboard Architecture

## 1. Общая архитектура

Проект реализует multi-domain платформу аналитики технологических трендов.

Архитектура пайплайна:

Raw Data
    ↓
ETL
    ↓
Aggregation Pipeline
    ↓
Trend Metrics
    ↓
Processed Layer
    ↓
FastAPI
    ↓
Streamlit Dashboard

---

## 2. Multi-domain architecture

В проекте реализованы два независимых технологических домена:

- semiconductors
- gene engineering

Каждый домен имеет:

- собственный raw слой
- собственный aggregation pipeline
- собственный time lag pipeline
- собственный API
- собственный Streamlit dashboard

---

## 3. Структура данных

### RAW слой

```text
src/data/raw/
├── openalex.parquet
├── patents.parquet
├── gene_engineering/
│   ├── openalex_ge.parquet
│   └── patents_ge.parquet
Processed слой
src/data/processed/
├── trend.parquet
├── trend_ge.parquet
├── trend_score.csv
└── speed_score.csv
Time Lag слой
src/data/time_lag/
├── time_lag.csv
└── time_lag_ge.csv
4. API architecture

Для каждого домена реализован отдельный FastAPI сервис.

API файлы
src/api/main.py
src/api/main_ge.py
Реализованные endpoints
/health
/topics
/topic_card
/lag_stats
/lag_distribution
5. Dashboard architecture

Для каждого домена реализован отдельный Streamlit dashboard.

Dashboard файлы
src/dashboard/app.py
src/dashboard/app_ge.py
Dashboard functionality

Дашборды отображают:

KPI cards
Trend Score
Publications dynamics
Patent dynamics
Time Lag distribution
6. Docker architecture

Проект упакован в Docker через docker-compose.yml.

Были созданы 4 контейнера:

Контейнер	Назначение	Порт
api_semiconductors	FastAPI для semiconductors	8001
api_gene_engineering	FastAPI для gene engineering	8002
dashboard_semiconductors	Streamlit dashboard semiconductors	8506
dashboard_gene_engineering	Streamlit dashboard gene engineering	8508

Docker orchestration обеспечивает независимый запуск API и dashboard сервисов для каждого домена.

7. Масштабируемость архитектуры

Архитектура проекта поддерживает добавление новых технологических доменов через создание отдельных:

raw datasets
aggregation pipelines
API services
Streamlit dashboards

Текущая структура позволяет масштабировать платформу без изменения существующих доменов.

8. Итог

В рамках MVP была реализована multi-domain аналитическая платформа для мониторинга технологических трендов с использованием:

FastAPI
Streamlit
Pandas
Plotly
Docker
Docker Compose

Проект поддерживает независимые аналитические пайплайны и dashboard-интерфейсы для различных технологических направлений.
