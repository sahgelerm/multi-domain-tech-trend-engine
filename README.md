## Multi-Domain Tech Trend Engine

Проект разрабатывался как внутренняя platform-архитектура внутри существующего исследовательского репозитория стажировки.
В рамках работы была реализована новая production-style multi-domain структура проекта.

## О проекте

Проект представляет собой production-style MVP аналитической платформы, реализующей полный цикл:

```text
OpenAlex / Patents
        ↓
      ETL
        ↓
 Aggregation
        ↓
 Trend Metrics
        ↓
 FastAPI
        ↓
 Streamlit

```
Платформа поддерживает multi-domain архитектуру и позволяет независимо масштабировать технологические домены.

Реализованные домены:

•	Semiconductors

•	Gene Engineering

Каждый домен изолирован:

•	на уровне raw-данных,

•	ETL pipeline,

•	aggregation pipeline,

•	API,

•	dashboard layer,

•	processed datasets.

## Преимущества архитектуры

• Масштабируемость — возможность добавления новых технологических доменов.

• Модульность — независимое расширение ETL, analytics и API слоев без изменения общей архитектуры.

• Гибкость аналитики — возможность подключения новых метрик, dashboard-компонентов и аналитических пайплайнов.

## Архитектура проекта

```text
src/
├── analytics
├── api
├── dashboard
├── data
├── data_sources
├── domains
├── etl
└── pipelines
```
## Tech Stack
```text
Core
• Python

Data & ETL
• OpenAlex API
• Pandas
• Parquet
• BigQuery

Backend
• FastAPI
• REST API

Frontend
• Streamlit
• Plotly

Infrastructure
• Docker
• AWS EC2
```
## Основные возможности:

## Data Engineering

•	ETL pipelines

•	parquet processing

•	monthly aggregation

•	time series generation

## Data Processing & SQL
```text
• Объединение данных - операции слияния/группировки (data joins - merge / groupby operations)

• Нормализация данных и выравнивание схемы (data normalization and schema alignment)

• Обработка интеграции данных из нескольких источников (handling multi-source data integration (OpenAlex + Patents))

• Аналитические преобразования - агрегация, фильтрация, временные ряды (analytical transformations - aggregation, filtering, time series)

• Обработка данных на основе SQL (SQL-based data processing (BigQuery))
```
## Analytics

•	trend metrics engine

•	trend_score

•	speed_score

•	time lag analytics

•	rolling smoothing

•	acceleration metrics

## Backend
```text
• FastAPI

• REST API (multi-domain endpoints)

• API design and routing

• caching strategies

• data serialization (JSON responses)

• API testing and validation

• production-ready endpoint structuring
```
## Testing & Validation
```text
• data validation during ETL (проверка схемы, проверка корректности)

• pipeline testing (DataLoader, проверка загрузки данных)

• API testing (проверка конечных точек, проверка ответов)

• Отладка и обработка ошибок в производственной среде
```
## Frontend

•	Streamlit dashboards

•	KPI cards

•	Plotly visualizations

## Infrastructure

•	AWS EC2

•	Docker

•	docker-compose

•	Linux deployment

## Docker Architecture

| Container | Port |
|---|---|
| api_semiconductors | 8001 |
| api_gene_engineering | 8002 |
| dashboard_semiconductors | 8506 |
| dashboard_gene_engineering | 8508 |

## Development Workflow
```text
Проект разрабатывался с использованием multi-branch workflow:

Основная ветвь:
• analytics-mvp — основная продуктовая разработка

Ветви исследований и экспериментов:
• doi_linkage_mvp — эксперименты по установлению связей DOI и извлечению NPL
• science-patents — исследования по интеграции патентов и научных публикаций
• tech-trend-engine — прототипы ранней архитектуры аналитики трендов

Структура ветвей использовалась для изоляции экспериментальных конвейеров, проверки альтернативных аналитических подходов и поддержки итеративной разработки платформы без влияния на стабильную архитектуру MVP.
```
## Dashboard Preview

### Semiconductors Dashboard

![Semiconductors Dashboard](docs/images/dashboard_semiconductors.png)

### Gene Engineering Dashboard

![Gene Engineering Dashboard](docs/images/dashboard_gene_engineering.png)

