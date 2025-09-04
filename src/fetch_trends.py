# src/fetch_trends.py
from datetime import datetime
from pathlib import Path
import time, random
import pandas as pd
from sqlalchemy import create_engine
from pytrends.request import TrendReq
from pytrends import exceptions as pt_exc

DB_URL = "sqlite:///db/trends.db"

def _interest_over_time_once(keywords, timeframe, geo):
    pytrends = TrendReq(hl="en-US", tz=0)
    pytrends.build_payload(kw_list=keywords, timeframe=timeframe, geo=geo)
    df = pytrends.interest_over_time()
    return df

def _with_backoff(func, *args, **kwargs):
    # up to 4 tries: 0s, 2s, 4s, 8s (+ jitter)
    for attempt in range(4):
        try:
            return func(*args, **kwargs)
        except pt_exc.TooManyRequestsError:
            if attempt == 3:
                raise
            sleep_s = (2 ** attempt) + random.uniform(0, 0.7)
            time.sleep(sleep_s)

def fetch_interest_over_time(keywords, timeframe="today 3-m", geo="US"):
    """
    Fetch Google Trends interest-over-time and persist to SQLite.
    - Retries with backoff on 429
    - Dedups rows per (date_ts, keyword)
    """
    if not keywords:
        return pd.DataFrame()

    # pytrends supports up to 5 keywords per payload reliably
    chunks = [keywords[i:i+5] for i in range(0, len(keywords), 5)]
    frames = []
    for chunk in chunks:
        df = _with_backoff(_interest_over_time_once, chunk, timeframe, geo)
        if df is None or df.empty:
            continue
        df = df.reset_index().rename(columns={"date": "date_ts"})
        if "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])
        long_df = df.melt(id_vars=["date_ts"], var_name="keyword", value_name="interest")
        long_df["fetched_at"] = pd.Timestamp.utcnow()
        frames.append(long_df)

    if not frames:
        return pd.DataFrame()

    long_df = pd.concat(frames, ignore_index=True)
    long_df = long_df.drop_duplicates(subset=["date_ts", "keyword"])

    # Ensure folders exist
    Path("db").mkdir(parents=True, exist_ok=True)
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)

    # Snapshots
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    # Save one representative raw/processed snapshot (optional)
    long_df.to_csv(f"data/processed/google_trends_long_{ts}.csv", index=False)

    # Persist to SQLite
    engine = create_engine(DB_URL, future=True)
    long_df.to_sql("topics", engine, if_exists="append", index=False)

    return long_df
