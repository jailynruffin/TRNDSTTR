# src/fetch_trends.py
from datetime import datetime
from pathlib import Path
import time, random
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.types import Integer, Float, String, DateTime
from pytrends.request import TrendReq
from pytrends import exceptions as pt_exc

DATA_DIR = Path("/mount/data")
RAW_DIR = DATA_DIR / "data" / "raw"
PROC_DIR = DATA_DIR / "data" / "processed"
for d in (DATA_DIR, RAW_DIR, PROC_DIR):
    d.mkdir(parents=True, exist_ok=True)

DB_URL = f"sqlite:///{(DATA_DIR / 'trndsttr.sqlite')}"
engine = create_engine(DB_URL, future=True)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    date_ts INTEGER NOT NULL,
    interest REAL,
    fetched_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_topics_date ON topics(date_ts);
CREATE INDEX IF NOT EXISTS idx_topics_kw_date ON topics(keyword, date_ts);
"""
with engine.begin() as conn:
    for stmt in SCHEMA_SQL.strip().split(";"):
        if stmt.strip():
            conn.exec_driver_sql(stmt)

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

    # up to 5 keywords per payload reliably
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
        long_df["date_ts"] = pd.to_datetime(long_df["date_ts"], utc=True, errors="coerce")
        long_df = long_df.dropna(subset=["date_ts"])
        long_df["date_ts"] = (long_df["date_ts"].view("int64") // 10**9).astype("int64")
        long_df["keyword"] = long_df["keyword"].astype("string")
        long_df["interest"] = pd.to_numeric(long_df["interest"], errors="coerce")
        long_df["fetched_at"] = pd.Timestamp.utcnow()
        frames.append(long_df)

    if not frames:
        return pd.DataFrame()

    long_df = pd.concat(frames, ignore_index=True)
    long_df = long_df.drop_duplicates(subset=["date_ts", "keyword"])

    # Ensure folders exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    # Snapshots
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    # Save one representative raw/processed snapshot 
    long_df.to_csv(PROC_DIR / f"google_trends_long_{ts}.csv", index=False)

    # Persist to SQLite
    dtype = {
        "keyword": String(),
        "date_ts": Integer(),
        "interest": Float(),
        "fetched_at": DateTime(timezone=False),
    }
    long_df.to_sql("topics", engine, if_exists="append", index=False, dtype=dtype, method="multi", chunksize=1000)

    return long_df

