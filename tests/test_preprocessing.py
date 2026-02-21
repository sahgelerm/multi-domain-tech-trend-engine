"""
Запуск: python tests/test_preprocessing.py
"""
import os
import sys
import pandas as pd
import tempfile

sys.path.append('.')
from etl.preprocessing import clean_domain_data


def make_raw_parquet(tmp_dir, domain, records):
    """Создаёт тестовый parquet в нужной структуре папок."""
    domain_dir = os.path.join(tmp_dir, domain)
    os.makedirs(domain_dir, exist_ok=True)
    df = pd.DataFrame(records)
    df.to_parquet(os.path.join(domain_dir, domain + "_batch_001.parquet"), index=False)
    return domain_dir


def make_test_records():
    """Возвращает тестовые записи с разными проблемами."""
    return [
        # Нормальные записи
        {"id": "W001", "title": "Paper A", "abstract": "text a", "year": 2020},
        {"id": "W002", "title": "Paper B", "abstract": "text b", "year": 2021},
        # Дубликат W002
        {"id": "W002", "title": "Paper B", "abstract": "text b", "year": 2021},
        # Без title
        {"id": "W003", "title": None,      "abstract": "text c", "year": 2022},
        # Без abstract
        {"id": "W004", "title": "Paper D", "abstract": "",        "year": 2023},
        # Пустой title (пробелы)
        {"id": "W005", "title": "   ",     "abstract": "text e", "year": 2023},
    ]


def test_removes_duplicates():
    """Дубликаты по id должны удаляться."""
    with tempfile.TemporaryDirectory() as tmp:
        make_raw_parquet(tmp, "test_domain", make_test_records())
        df = clean_domain_data("test_domain", tmp, tmp, require_abstract=False)
        assert df["id"].nunique() == len(df), "Остались дубликаты"
        assert "W002" in df["id"].values, "W002 должен остаться (один раз)"
    print("Дубликаты удаляются — OK")


def test_removes_empty_title():
    """Записи без title и с пустым title должны удаляться."""
    with tempfile.TemporaryDirectory() as tmp:
        make_raw_parquet(tmp, "test_domain", make_test_records())
        df = clean_domain_data("test_domain", tmp, tmp, require_abstract=False)
        assert "W003" not in df["id"].values, "W003 (None title) должен быть удалён"
        assert "W005" not in df["id"].values, "W005 (пустой title) должен быть удалён"
    print("Пустые title удаляются — OK")


def test_removes_empty_abstract():
    """Записи без abstract удаляются если require_abstract=True."""
    with tempfile.TemporaryDirectory() as tmp:
        make_raw_parquet(tmp, "test_domain", make_test_records())
        df = clean_domain_data("test_domain", tmp, tmp, require_abstract=True)
        assert "W004" not in df["id"].values, "W004 (пустой abstract) должен быть удалён"
    print("Пустые abstract удаляются — OK")


def test_keeps_abstract_if_not_required():
    """Если require_abstract=False — записи без abstract остаются."""
    with tempfile.TemporaryDirectory() as tmp:
        make_raw_parquet(tmp, "test_domain", make_test_records())
        df = clean_domain_data("test_domain", tmp, tmp, require_abstract=False)
        assert "W004" in df["id"].values, "W004 должен остаться при require_abstract=False"
    print("require_abstract=False работает — OK")


def test_clean_result_has_no_issues():
    """После очистки не должно быть никаких проблем в данных."""
    with tempfile.TemporaryDirectory() as tmp:
        make_raw_parquet(tmp, "test_domain", make_test_records())
        df = clean_domain_data("test_domain", tmp, tmp, require_abstract=True)
        assert df["id"].nunique() == len(df)
        assert df["title"].isna().sum() == 0
        assert df["abstract"].eq("").sum() == 0
    print("Итоговые данные чистые — OK")


def test_raises_if_no_files():
    """Должна быть ошибка если батчей нет."""
    with tempfile.TemporaryDirectory() as tmp:
        try:
            clean_domain_data("nonexistent", tmp, tmp)
            assert False, "Должна была быть ошибка FileNotFoundError"
        except FileNotFoundError:
            pass
    print("FileNotFoundError при отсутствии батчей — OK")


def test_saves_parquet_to_processed_dir():
    """Проверяет что очищенный файл сохраняется в processed_dir."""
    with tempfile.TemporaryDirectory() as tmp:
        raw_dir  = os.path.join(tmp, "raw")
        proc_dir = os.path.join(tmp, "processed")
        make_raw_parquet(raw_dir, "test_domain", make_test_records())
        clean_domain_data("test_domain", raw_dir, proc_dir, require_abstract=False)
        expected_path = os.path.join(proc_dir, "test_domain_clean.parquet")
        assert os.path.exists(expected_path), "Файл не сохранён в processed_dir"
    print("Parquet сохраняется корректно — OK")


if __name__ == "__main__":
    print("Тесты preprocessing.py\n")
    test_removes_duplicates()
    test_removes_empty_title()
    test_removes_empty_abstract()
    test_keeps_abstract_if_not_required()
    test_clean_result_has_no_issues()
    test_raises_if_no_files()
    test_saves_parquet_to_processed_dir()
    print("Все тесты прошли!")