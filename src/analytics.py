# src/analytics.py
import pandas as pd
from sqlalchemy import text
from .db import engine

def distinct_keywords():
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT DISTINCT keyword FROM topics ORDER BY keyword")).all()
    return [r[0] for r in rows]

def max_timestamp():
    with engine.begin() as conn:
        return pd.to_datetime(conn.execute(text("SELECT MAX(date_ts) FROM topics")).scalar())

def _in_clause(keys):
    # returns (sql, params) e.g. "(:k0,:k1)" and {"k0": "...", "k1": "..."}
    return "(" + ",".join([f":k{i}" for i in range(len(keys))]) + ")", {f"k{i}": k for i, k in enumerate(keys)}

def kpis(filter_keywords: list[str] | None = None, last_days=7):
    d0 = max_timestamp()
    if pd.isna(d0): 
        return None
    params = {"d0": d0.to_pydatetime(),
              "d7": (d0 - pd.Timedelta(days=last_days)).to_pydatetime(),
              "d14": (d0 - pd.Timedelta(days=2*last_days)).to_pydatetime()}
    kw_sql = ""
    if filter_keywords:
        sql_in, kw_params = _in_clause(filter_keywords)
        kw_sql = f" AND keyword IN {sql_in} "
        params.update(kw_params)

    last7 = pd.read_sql(text(f"""
        SELECT keyword, AVG(interest) AS avg7
        FROM topics
        WHERE date_ts > :d7 AND date_ts <= :d0 {kw_sql}
        GROUP BY keyword
    """), engine, params=params)

    prev7 = pd.read_sql(text(f"""
        SELECT keyword, AVG(interest) AS avg_prev7
        FROM topics
        WHERE date_ts > :d14 AND date_ts <= :d7 {kw_sql}
        GROUP BY keyword
    """), engine, params=params)

    kpi = last7.merge(prev7, on="keyword", how="left").fillna({"avg_prev7": 0})
    kpi["delta"] = kpi["avg7"] - kpi["avg_prev7"]
    kpi["pct_change"] = (kpi["delta"] / kpi["avg_prev7"].replace(0, pd.NA)) * 100
    return kpi

def timeseries_for(keywords: list[str]):
    if not keywords: 
        return None
    sql_in, params = _in_clause(keywords)
    q = f"""
        SELECT date_ts, keyword, AVG(interest) AS interest
        FROM topics
        WHERE keyword IN {sql_in}
        GROUP BY date_ts, keyword
        ORDER BY date_ts
    """
    return pd.read_sql(text(q), engine, params=params, parse_dates=["date_ts"])
