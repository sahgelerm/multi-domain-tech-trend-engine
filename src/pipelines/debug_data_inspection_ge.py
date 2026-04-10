import pandas as pd
import os

# ==============================
# CONFIG (GE DOMAIN)
# ==============================

OPENALEX_PATH = "/home/ubuntu/OpenAlex"
PATENTS_PATH = "/home/ubuntu/patents/ge"

print("=== CHECK PATHS ===")

print("OpenAlex exists:", os.path.exists(OPENALEX_PATH))
print("Patents GE exists:", os.path.exists(PATENTS_PATH))


# ==============================
# LIST OPENALEX FILES
# ==============================

print("\n=== OPENALEX FILES ===")

try:
    oa_files = os.listdir(OPENALEX_PATH)
    for f in oa_files:
        print(f)
except Exception as e:
    print("Error reading OpenAlex:", e)


# ==============================
# LIST PATENTS GE FILES
# ==============================

print("\n=== GE PATENTS FILES ===")

try:
    patent_files = os.listdir(PATENTS_PATH)
    for f in patent_files:
        print(f)
except Exception as e:
    print("Error reading patents:", e)


# ==============================
# LOAD SAMPLE FILES (SAFE)
# ==============================

print("\n=== LOADING SAMPLE FILES ===")

try:
    patents_file = os.path.join(PATENTS_PATH, "patents.parquet")
    citation_file = os.path.join(PATENTS_PATH, "citation.parquet")

    df_patents = pd.read_parquet(patents_file)
    df_citations = pd.read_parquet(citation_file)

    print("\nPatents shape:", df_patents.shape)
    print("Patents columns:")
    print(df_patents.columns)

    print("\nCitations shape:", df_citations.shape)
    print("Citations columns:")
    print(df_citations.columns)

    print("\nPatents sample:")
    print(df_patents.head(2))

    print("\nCitations sample:")
    print(df_citations.head(2))

except Exception as e:
    print("Error loading data:", e)
