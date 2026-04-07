from fastapi import FastAPI
import pandas as pd

app = FastAPI()

DATA_PATH = "data/processed/trend.parquet"


@app.get("/topic_card")
def get_topic(topic: str):
    df = pd.read_parquet(DATA_PATH)

    df = df[df["topic_name"] == topic]

    return df.tail(12).to_dict(orient="records")

