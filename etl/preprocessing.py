import os
import glob
import pandas as pd

def clean_domain_data(domain, raw_dir, processed_dir, require_abstract=True):
    """
    Минимальная чистка данных домена:
    - удаление дубликатов по id
    - удаление записей без title
    - опционально: удаление записей без abstract (для NLP-задач)

    Args:
        domain: 'semiconductors' / 'gene_engineering'
        raw_dir: папка с сырыми батчами
        processed_dir: папка для сохранения очищенных данных
        require_abstract: если True — удаляем записи с пустым abstract
    """
    # Загружаем все батчи
    files = glob.glob(os.path.join(raw_dir, domain, "*.parquet"))
    if not files:
        raise FileNotFoundError("Батчи не найдены в: " + os.path.join(raw_dir, domain))

    df = pd.concat([pd.read_parquet(f) for f in sorted(files)], ignore_index=True)
    initial_count = len(df)
    print("Домен: " + domain)
    print("Загружено записей: " + f"{initial_count:,}")

    # 1. Дубликаты по id
    before = len(df)
    df = df.drop_duplicates(subset=["id"])
    dupes = before - len(df)
    print("Удалено дубликатов: " + f"{dupes:,}")

    # 2. Записи без title
    before = len(df)
    df = df[df["title"].notna() & df["title"].str.strip().ne("")]
    print("Удалено без title: " + f"{before - len(df):,}")

    # 3. Записи без abstract
    if require_abstract:
        before = len(df)
        df = df[df["abstract"].notna() & df["abstract"].str.strip().ne("")]
        print("Удалено без abstract: " + f"{before - len(df):,}")

    print("Осталось записей: " + f"{len(df):,}")
    print("Потери: " + f"{(1 - len(df)/initial_count)*100:.1f}%")

    # Сохраняем
    os.makedirs(processed_dir, exist_ok=True)
    out_path = os.path.join(processed_dir, domain + "_clean.parquet")
    df.to_parquet(out_path, index=False)
    print("Сохранено: " + out_path + "\n")
    return df