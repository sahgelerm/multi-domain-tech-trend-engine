"""
Запуск: python tests/test_openalex_client.py
"""
import os
import sys
import json
import tempfile

sys.path.append('.')
from etl.openalex_client import parse_work, _save_cursor, _load_cursor


def test_parse_work_basic():
    """parse_work должен корректно извлекать основные поля."""
    work = {
        "id": "W123",
        "title": "Test Paper",
        "publication_date": "2022-05-15",
        "publication_year": 2022,
        "cited_by_count": 42,
        "doi": "10.1234/test",
        "type": "article",
        "abstract_inverted_index": None,
        "primary_topic": {"id": "T001", "display_name": "Semiconductors"},
        "authorships": [],
        "open_access": {"is_oa": True}
    }
    result = parse_work(work)
    assert result["id"] == "W123"
    assert result["title"] == "Test Paper"
    assert result["year"] == 2022
    assert result["cited_by_count"] == 42
    assert result["topic_id"] == "T001"
    assert result["open_access"] == True
    print("parse_work базовые поля — OK")


def test_parse_work_reconstructs_abstract():
    """parse_work должен восстанавливать абстракт из inverted index."""
    work = {
        "id": "W124",
        "title": "Paper",
        "publication_date": "2022-01-01",
        "publication_year": 2022,
        "cited_by_count": 0,
        "doi": "",
        "type": "article",
        "abstract_inverted_index": {
            "Hello": [0],
            "world": [1],
            "test": [2]
        },
        "primary_topic": None,
        "authorships": [],
        "open_access": {"is_oa": False}
    }
    result = parse_work(work)
    assert result["abstract"] == "Hello world test"
    print("parse_work восстанавливает абстракт — OK")


def test_parse_work_empty_abstract():
    """parse_work должен вернуть пустую строку если нет абстракта."""
    work = {
        "id": "W125",
        "title": "Paper",
        "publication_date": "2022-01-01",
        "publication_year": 2022,
        "cited_by_count": 0,
        "doi": "",
        "type": "article",
        "abstract_inverted_index": None,
        "primary_topic": None,
        "authorships": [],
        "open_access": {"is_oa": False}
    }
    result = parse_work(work)
    assert result["abstract"] == ""
    print("parse_work пустой абстракт — OK")


def test_parse_work_extracts_institutions():
    """parse_work должен собирать уникальные институции авторов."""
    work = {
        "id": "W126",
        "title": "Paper",
        "publication_date": "2022-01-01",
        "publication_year": 2022,
        "cited_by_count": 0,
        "doi": "",
        "type": "article",
        "abstract_inverted_index": None,
        "primary_topic": None,
        "open_access": {"is_oa": False},
        "authorships": [
            {"institutions": [{"display_name": "MIT"}]},
            {"institutions": [{"display_name": "Stanford"}]},
            # Дубликат — должен остаться один раз
            {"institutions": [{"display_name": "MIT"}]},
        ]
    }
    result = parse_work(work)
    institutions = result["institutions"].split("; ")
    assert len(institutions) == 2, "Дубликаты институций не удалены"
    assert "MIT" in institutions
    assert "Stanford" in institutions
    print("parse_work извлекает уникальные институции — OK")


def test_cursor_save_and_load():
    """_save_cursor и _load_cursor должны корректно сохранять состояние."""
    with tempfile.TemporaryDirectory() as tmp:
        cursor_path = os.path.join(tmp, "test_cursor.json")
        _save_cursor(cursor_path, "abc123", 3, 150000)
        cursor, batch_num, total = _load_cursor(cursor_path)
        assert cursor == "abc123"
        assert batch_num == 3
        assert total == 150000
    print("Курсор сохраняется и загружается — OK")


def test_load_cursor_default_if_missing():
    """_load_cursor должен возвращать дефолтные значения если файла нет."""
    with tempfile.TemporaryDirectory() as tmp:
        cursor_path = os.path.join(tmp, "nonexistent.json")
        cursor, batch_num, total = _load_cursor(cursor_path)
        assert cursor == "*"
        assert batch_num == 1
        assert total == 0
    print("Дефолтные значения курсора если файла нет — OK")


if __name__ == "__main__":
    print("Тесты openalex_client.py\n")
    test_parse_work_basic()
    test_parse_work_reconstructs_abstract()
    test_parse_work_empty_abstract()
    test_parse_work_extracts_institutions()
    test_cursor_save_and_load()
    test_load_cursor_default_if_missing()
    print("Все тесты прошли!")