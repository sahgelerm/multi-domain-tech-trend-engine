import pandas as pd
import os

# ==============================
# CONFIG
# ==============================

OPENALEX_PATH = "/home/ubuntu/OpenAlex/semiconductors_clean_signal.parquet"
PATENTS_PATH = "/home/ubuntu/patents/semiconductors"


# ==============================
# OPENALEX
# ==============================

print("=== OPENALEX DATA ===")

df_openalex = pd.read_parquet(OPENALEX_PATH)

print("Shape:", df_openalex.shape)
print("\nColumns:")
print(df_openalex.columns)

print("\nSample:")
print(df_openalex.head(2))


# ==============================
# PATENTS (список файлов)
# ==============================

print("\n=== PATENTS FILES ===")

files = os.listdir(PATENTS_PATH)
for f in files:
    print(f)

# ==============================
# ЗАГРУЗКА ТОЛЬКО НУЖНЫХ ФАЙЛОВ
# ==============================

print("\n=== LOADING PATENTS DATA ===")

# ⚠️ НЕ грузим abstract_localized.parquet (очень тяжелый)

patents_file = os.path.join(PATENTS_PATH, "patents.parquet")
cpc_file = os.path.join(PATENTS_PATH, "cpc.parquet")

df_patents = pd.read_parquet(patents_file)
df_cpc = pd.read_parquet(cpc_file)

print("\nPatents shape:", df_patents.shape)
print("CPC shape:", df_cpc.shape)

print("\nPatents columns:")
print(df_patents.columns)

print("\nCPC columns:")
print(df_cpc.columns)

print("\nPatents sample:")
print(df_patents.head(2))

print("\nCPC sample:")
print(df_cpc.head(2))

