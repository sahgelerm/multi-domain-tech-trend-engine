"""
End-to-end тест пайплайна Задачи 1.
На отдельном тестовом домене (Batteries).
Запуск: python tests/test_e2e_pipeline.py
"""
import os
import sys
import shutil
import pandas as pd

sys.path.append('.')

from etl.openalex_client import collect_works, load_domain_config
from etl.preprocessing import clean_domain_data
from etl.metrics import calc_domain_summary, print_domain_summary
from visualization.charts import plot_publications_dynamics

# Конфигурация тестового домена
# T10175 = Energy Storage / Batteries 
# Один топик, 5 лет 
TEST_DOMAIN_KEY  = "batteries_test"
TEST_DOMAIN_CONFIG = {
    "display_name": "Batteries (TEST)",
    "color": "#ff7f0e",
    "openalex_topic_ids": ["T10175"],
    "cpc_codes": ["H01M", "H02J"]
}
TEST_YEAR_FROM = 2019
TEST_YEAR_TO   = 2023

TEST_RAW_DIR   = "tests/e2e_data/raw/batteries_test"
TEST_PROC_DIR  = "tests/e2e_data/processed"


def patch_config():
    """Временно добавляет тестовый домен в domains.json."""
    import json
    config_path = 'config/domains.json'
    with open(config_path) as f:
        config = json.load(f)

    # Сохраняем оригинал
    original = dict(config)

    config[TEST_DOMAIN_KEY] = TEST_DOMAIN_CONFIG
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return original


def restore_config(original):
    """Восстанавливает оригинальный domains.json."""
    import json
    config_path = 'config/domains.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(original, f, ensure_ascii=False, indent=2)
    print("domains.json восстановлен.")


def cleanup_test_data():
    """Удаляет тестовые данные с подтверждением"""
    test_dir = "tests/e2e_data"
    if not os.path.exists(test_dir):
        return

    print("Тест завершён.")
    print("Тестовые данные находятся в: " + test_dir)
    answer = input("Удалить тестовые данные? (да/нет): ").strip().lower()

    if answer in ["да", "y", "yes", "д"]:
        shutil.rmtree(test_dir)
        print("Тестовые данные удалены.")
    else:
        print("Тестовые данные сохранены в: " + test_dir)      


def step_1_collect():
    """Шаг 1: Сбор данных из OpenAlex."""
    print("[ Шаг 1: Сбор данных ]")
    total = collect_works(
        domain=TEST_DOMAIN_KEY,
        save_dir=TEST_RAW_DIR,
        year_from=TEST_YEAR_FROM,
        year_to=TEST_YEAR_TO
    )
    assert total > 0, "Не собрано ни одной статьи"
    assert os.path.exists(TEST_RAW_DIR), "Папка с батчами не создана"

    files = [f for f in os.listdir(TEST_RAW_DIR) if f.endswith(".parquet")]
    assert len(files) > 0, "Parquet файлы не созданы"

    print("Шаг 1 — OK | Собрано: " + f"{total:,}" + " статей")
    return total


def step_2_clean(raw_total):
    """Шаг 2: Очистка данных."""
    print("[ Шаг 2: Очистка данных ]")
    df = clean_domain_data(
        domain=TEST_DOMAIN_KEY,
        raw_dir="tests/e2e_data/raw",
        processed_dir=TEST_PROC_DIR
    )

    out_path = os.path.join(TEST_PROC_DIR, TEST_DOMAIN_KEY + "_clean.parquet")
    assert os.path.exists(out_path), "Очищенный файл не создан"
    assert len(df) > 0, "После очистки не осталось данных"
    assert len(df) <= raw_total, "После очистки записей больше чем до неё"
    assert df["id"].nunique() == len(df), "В очищенных данных есть дубликаты"
    assert df["title"].isna().sum() == 0, "В очищенных данных есть пустые title"
    assert df["abstract"].eq("").sum() == 0, "В очищенных данных есть пустые abstract"

    print("Шаг 2 — OK | После очистки: " + f"{len(df):,}" + " статей")
    return df


def step_3_metrics(df):
    """Шаг 3: Расчёт метрик."""
    print("[ Шаг 3: Метрики ]")
    df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce")
    df["period"] = df["publication_date"].dt.to_period("M")

    monthly = df.groupby("period").size().reset_index(name="count")
    monthly["period_dt"] = monthly["period"].dt.to_timestamp()
    yearly = df[df["year"] <= TEST_YEAR_TO].groupby("year").size().reset_index(name="count")

    # Проверяем что есть данные за все 5 лет
    years_in_data = sorted(yearly["year"].tolist())
    expected_years = list(range(TEST_YEAR_FROM, TEST_YEAR_TO + 1))
    assert years_in_data == expected_years, (
        "Ожидались годы " + str(expected_years) +
        ", получили " + str(years_in_data)
    )

    summary = calc_domain_summary(
        TEST_DOMAIN_KEY,
        TEST_DOMAIN_CONFIG["display_name"],
        yearly,
        monthly
    )

    # Проверяем все поля
    required_fields = ["total", "cagr", "yoy_last", "acceleration",
                       "peak_year", "peak_count"]
    for field in required_fields:
        assert field in summary, "Нет поля: " + field

    assert summary["total"] > 0, "Total = 0"
    assert summary["first_year"] == TEST_YEAR_FROM
    assert summary["last_year"]  == TEST_YEAR_TO

    print_domain_summary(summary)
    print("Шаг 3 — OK")
    return summary, yearly, monthly


def step_4_visualization(summary, yearly, monthly):
    """Шаг 4: Построение графика."""
    print("[ Шаг 4: Визуализация ]")
    fig = plot_publications_dynamics(
        domain_key=TEST_DOMAIN_KEY,
        label=TEST_DOMAIN_CONFIG["display_name"],
        color=TEST_DOMAIN_CONFIG["color"],
        monthly_df=monthly,
        yearly_df=yearly
    )
    assert fig is not None, "График не создан"

    # Проверяем что в графике есть данные
    assert len(fig.data) == 2, "Ожидалось 2 трейса (monthly + yearly)"
    assert len(fig.data[1].x) == 5, "Ожидалось 5 точек на годовом графике"

    print("Шаг 4 — OK | График построен")


if __name__ == "__main__":    
    print("END-TO-END ТЕСТ ПАЙПЛАЙНА (Задача 1)")
    print("Тестовый домен: Batteries (2019–2023)")
    
    original_config = None
    try:
        # Временно добавляем тестовый домен в конфиг
        original_config = patch_config()

        total    = step_1_collect()
        df       = step_2_clean(total)
        summary, yearly, monthly = step_3_metrics(df)
        step_4_visualization(summary, yearly, monthly)
      
        print("END-TO-END ТЕСТ ПРОШЁЛ УСПЕШНО")
        

    except Exception as e:
        print("ТЕСТ УПАЛ: " + str(e))
        raise

    finally:
        # Восстанавливаем конфиг в любом случае — даже если тест упал
        if original_config:
            restore_config(original_config)
        # Спрашиваем про удаление данных
        cleanup_test_data()