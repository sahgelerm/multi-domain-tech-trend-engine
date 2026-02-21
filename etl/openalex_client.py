import json
import time
import os
import requests
import pandas as pd

CONFIG_PATH = '/content/drive/MyDrive/semiconductor_project/config/domains.json'
HEADERS = {"User-Agent": "mailto:mail@gmail.com"} # Укажите свой email для идентификации при запросах к OpenAlex API


def load_domain_config(domain):
    """Загружает конфигурацию домена из domains.json."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    if domain not in config:
        raise ValueError("Домен '" + domain + "' не найден. Доступные: " + str(list(config.keys())))
    return config[domain]


def get_yearly_counts(topic_ids, year_from=2010, year_to=2025):
    """Возвращает количество статей по годам для заданных topic_ids."""
    topic_filter = "|".join(topic_ids)
    yearly_counts = {}
    for year in range(year_from, year_to + 1):
        params = {
            "filter": "topics.id:" + topic_filter + ",has_abstract:true,publication_year:" + str(year),
            "per-page": 1
        }
        try:
            r = requests.get("https://api.openalex.org/works", params=params, timeout=15)
            if r.status_code == 200:
                yearly_counts[year] = r.json()["meta"]["count"]
            else:
                print("  [" + str(year) + "] Ошибка " + str(r.status_code))
                yearly_counts[year] = None
        except requests.exceptions.RequestException as e:
            print("  [" + str(year) + "] Сетевая ошибка: " + str(e))
            yearly_counts[year] = None
        time.sleep(0.1)
    return yearly_counts


def print_yearly_counts(domain, counts):
    """Выводит таблицу с динамикой по годам."""
    print("Динамика публикаций — " + domain)
    print("Год      Количество")
    print("." * 25)
    total = 0
    for year, count in counts.items():
        if count is not None:
            total += count
            print(str(year) + "     " + f"{count:>12,}")
        else:
            print(str(year) + "     —")
    print("." * 25)
    print("ИТОГО    " + f"{total:>12,}")


def parse_work(work):
    """Извлекает нужные поля из одной статьи OpenAlex."""
    abstract = ""
    if work.get("abstract_inverted_index"):
        words_positions = [
            (pos, word)
            for word, positions in work["abstract_inverted_index"].items()
            for pos in positions
        ]
        abstract = " ".join(w for _, w in sorted(words_positions))

    primary_topic = work.get("primary_topic") or {}
    institutions = list({
        inst["display_name"]
        for authorship in work.get("authorships", [])
        for inst in authorship.get("institutions", [])
        if inst.get("display_name")
    })

    return {
        "id": work.get("id", ""),
        "title": work.get("title", ""),
        "abstract": abstract,
        "publication_date": work.get("publication_date", ""),
        "year": work.get("publication_year"),
        "cited_by_count": work.get("cited_by_count", 0),
        "doi": work.get("doi", ""),
        "topic_id": primary_topic.get("id", ""),
        "topic_name": primary_topic.get("display_name", ""),
        "institutions": "; ".join(institutions),
        "open_access": work.get("open_access", {}).get("is_oa", False),
        "type": work.get("type", "")
    }


def _save_cursor(cursor_path, cursor, batch_num, total):
    """Сохраняет состояние загрузки для возобновления после прерывания."""
    with open(cursor_path, 'w') as f:
        json.dump({"cursor": cursor, "batch_num": batch_num, "total": total}, f)


def _load_cursor(cursor_path):
    """Загружает сохранённое состояние. Возвращает (cursor, batch_num, total)."""
    if not os.path.exists(cursor_path):
        return "*", 1, 0
    with open(cursor_path, 'r') as f:
        state = json.load(f)
    print("Найдено сохранённое состояние: батч " + str(state['batch_num']) + ", собрано " + f"{state['total']:,}")
    return state["cursor"], state["batch_num"], state["total"]


def _fetch_page(filter_str, cursor):
    """Делает один запрос к API с повторными попытками."""
    params = {
        "filter": filter_str,
        "per-page": 200,
        "cursor": cursor,
        "select": "id,title,abstract_inverted_index,publication_date,publication_year,cited_by_count,doi,primary_topic,authorships,open_access,type"
    }
    for attempt in range(3):
        try:
            r = requests.get(
                "https://api.openalex.org/works",
                params=params,
                headers=HEADERS,
                timeout=30
            )
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:              
                time.sleep(60)
            else:
                print("Ошибка " + str(r.status_code) + ", попытка " + str(attempt + 1) + "/3")
                time.sleep(5)
        except requests.exceptions.RequestException as e:
            print("Сетевая ошибка: " + str(e) + ", попытка " + str(attempt + 1) + "/3")
            time.sleep(10)
    return None


def _save_manifest(save_dir, domain, topic_ids, total):
    """Сохраняет метаданные о том, что именно было скачано."""
    manifest = {
        "domain": domain,
        "topic_ids": topic_ids,
        "total_collected": total,
        "saved_at": pd.Timestamp.now().isoformat()
    }
    path = os.path.join(save_dir, domain + "_manifest.json")
    with open(path, 'w') as f:
        json.dump(manifest, f, indent=2)   


def _load_manifest(save_dir, domain):
    """Загружает предыдущий манифест если есть."""
    path = os.path.join(save_dir, domain + "_manifest.json")
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return json.load(f)


def collect_works(domain, save_dir, year_from=2010, year_to=2025, batch_size=50000):
    """
    Выгружает статьи из OpenAlex по домену и сохраняет батчами в Parquet.
    
    Поддерживает:
    - возобновление после прерывания (cursor.json)
    - инкрементальную догрузку при добавлении новых Topic IDs (manifest.json)

    Args:
        domain: ключ домена из domains.json ('semiconductors' / 'gene_engineering')
        save_dir: папка для сохранения батчей (отдельная для каждого домена)
        year_from: начальный год выборки
        year_to: конечный год выборки
        batch_size: сколько записей в одном parquet-файле
    """
    config = load_domain_config(domain)
    topic_ids = config["openalex_topic_ids"]

    os.makedirs(save_dir, exist_ok=True)

    # Проверяем: есть ли уже скачанные данные и не изменился ли список топиков
    manifest = _load_manifest(save_dir, domain)
    if manifest:
        old_ids = set(manifest["topic_ids"])
        new_ids = set(topic_ids)
        added = new_ids - old_ids

        if not added:
            print("Топики не изменились. Повторная загрузка не нужна.")
            print("Уже собрано: " + f"{manifest['total_collected']:,}" + " статей")
            return manifest["total_collected"]
        else:
            print("Найдены новые топики: " + str(added))
            print("Докачиваем только их...")
            # Для инкрементальной загрузки используем только новые топики
            topic_ids_to_fetch = list(added)
    else:
        topic_ids_to_fetch = topic_ids

    topic_filter = "|".join(topic_ids_to_fetch)
    filter_str = "topics.id:" + topic_filter + ",has_abstract:true,publication_year:" + str(year_from) + "-" + str(year_to)

    cursor_path = os.path.join(save_dir, domain + "_cursor.json")
    cursor, batch_num, total_collected = _load_cursor(cursor_path)

    # Если докачиваем — начинаем нумерацию батчей после существующих
    if manifest and batch_num == 1:
        existing = [f for f in os.listdir(save_dir) if f.endswith(".parquet")]
        batch_num = len(existing) + 1

    buffer = []
    print(config['display_name'] + " (" + str(year_from) + "-" + str(year_to) + ")")
    print("Фильтр: " + filter_str + "\n")

    while True:
        data = _fetch_page(filter_str, cursor)
        if data is None:
            print("Не удалось получить данные после 3 попыток")
            break

        results = data.get("results", [])
        if not results:            
            break

        buffer.extend(parse_work(w) for w in results)
        total_collected += len(results)
        cursor = data.get("meta", {}).get("next_cursor")

        if cursor:
            _save_cursor(cursor_path, cursor, batch_num, total_collected)

        if len(buffer) >= batch_size:
            filepath = os.path.join(save_dir, domain + "_batch_" + f"{batch_num:03d}" + ".parquet")
            pd.DataFrame(buffer).to_parquet(filepath, index=False)
            print("Батч " + f"{batch_num:03d}" + " сохранён | " + f"{len(buffer):,}" + " статей | всего: " + f"{total_collected:,}")
            buffer = []
            batch_num += 1

        if not cursor:            
            break

        time.sleep(0.1)

    if buffer:
        filepath = os.path.join(save_dir, domain + "_batch_" + f"{batch_num:03d}" + ".parquet")
        pd.DataFrame(buffer).to_parquet(filepath, index=False)
        print("Финальный батч " + f"{batch_num:03d}" + " сохранён | " + f"{len(buffer):,}" + " статей")

    if os.path.exists(cursor_path):
        os.remove(cursor_path)

    # Обновляем манифест с полным списком топиков (старые + новые)
    all_topic_ids = list(set(topic_ids) | set(manifest["topic_ids"] if manifest else []))
    final_total = total_collected + (manifest["total_collected"] if manifest else 0)
    _save_manifest(save_dir, domain, all_topic_ids, final_total)

    print("собрано: " + f"{total_collected:,}" + " статей")
    return total_collected