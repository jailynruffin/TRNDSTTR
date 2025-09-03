# src/fetch_trends.py
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from pytrends.request import TrendReq

DB_URL = "sqlite:///db/trends.db"

def fetch_interest_over_time(keywords, timeframe="today 3-m", geo="US"):
    """
    keywords: list[str]
    timeframe: e.g. "today 12-m", "today 3-m", "now 7-d"
    geo: "US" for United States, "" for worldwide
    """
    if not keywords:
        return pd.DataFrame()

    pytrends = TrendReq(hl="en-US", tz=0)
    pytrends.build_payload(kw_list=keywords, timeframe=timeframe, geo=geo)
    df = pytrends.interest_over_time()

    if df.empty:
        return df

    # Clean up
    df = df.reset_index().rename(columns={"date": "date_ts"})
    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])

    # Melt to long form: date | keyword | interest
    long_df = df.melt(id_vars=["date_ts"], var_name="keyword", value_name="interest")
    long_df["fetched_at"] = pd.Timestamp.utcnow()

    # Ensure folders exist
    Path("db").mkdir(parents=True, exist_ok=True)
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)

    # Save raw & processed snapshots
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    df.to_csv(f"data/raw/google_trends_raw_{ts}.csv", index=False)
    long_df.to_csv(f"data/processed/google_trends_long_{ts}.csv", index=False)

    # Persist to SQLite
    engine = create_engine(DB_URL, future=True)
    # Basic de-dup within this pull
    long_df = long_df.drop_duplicates(subset=["date_ts", "keyword"])
    long_df.to_sql("topics", engine, if_exists="append", index=False)

    return long_df
