import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path

from src.fetch_trends import fetch_interest_over_time

st.set_page_config(page_title="TRNDSTTR", layout="wide")
st.title("TRNDSTTR")
st.caption("Culture. Data. Insights.")

# --- Controls
with st.sidebar:
    st.header("Fetch Google Trends")
    default_keywords = ["Sabrina Carpenter", "Addison Rae", "Taylor Swift"]
    keywords_input = st.text_input(
        "Keywords (comma-separated)",
        value=", ".join(default_keywords),
        help="Example: Sabrina Carpenter, Addison Rae, Taylor Swift",
    )
    timeframe = st.selectbox(
        "Timeframe",
        ["now 7-d", "today 3-m", "today 12-m", "today 5-y"],
        index=1,
    )
    geo = st.selectbox("Region", ["US", ""], index=0, help="US or Worldwide ('').")
    fetch_btn = st.button("Fetch & Save")

# --- Action
if fetch_btn:
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
    with st.spinner("Pulling Google Trends..."):
        df = fetch_interest_over_time(keywords, timeframe=timeframe, geo=geo)
    if df.empty:
        st.error("No data returned. Try different keywords or timeframe.")
    else:
        st.success(f"Fetched {len(df)} rows and saved to SQLite.")
        st.dataframe(df.head())

# --- Display from DB (so you can see history persists)
Path("db").mkdir(parents=True, exist_ok=True)
engine = create_engine("sqlite:///db/trends.db", future=True)

st.subheader("Interest over time (from database)")
keywords_for_view = st.multiselect(
    "Select keywords to visualize",
    options=[],
    default=[],
    placeholder="Fetch once or type keywords above first",
)

# If no multiselect choices yet, try to read them from DB
if not keywords_for_view:
    try:
        with engine.begin() as conn:
            rows = conn.execute(text("SELECT DISTINCT keyword FROM topics ORDER BY keyword")).all()
        all_keywords = [r[0] for r in rows]
        if all_keywords:
            keywords_for_view = st.multiselect(
                "Select keywords to visualize",
                options=all_keywords,
                default=all_keywords[:3],
            )
    except Exception:
        pass

if keywords_for_view:
    query = """
        SELECT date_ts, keyword, interest
        FROM topics
        WHERE keyword IN ({})
        ORDER BY date_ts ASC
    """.format(",".join([f":k{i}" for i in range(len(keywords_for_view))]))
    params = {f"k{i}": k for i, k in enumerate(keywords_for_view)}
    df_db = pd.read_sql(text(query), engine, params=params, parse_dates=["date_ts"])

    if df_db.empty:
        st.info("No rows yet—click Fetch & Save in the sidebar.")
    else:
        # Wide-to-long for Streamlit line_chart
        pivot = df_db.pivot(index="date_ts", columns="keyword", values="interest").sort_index()
        st.line_chart(pivot, height=380, use_container_width=True)
        st.caption(f"{len(df_db)} rows • {len(keywords_for_view)} keywords • timeframe varies by fetches")
else:
    st.info("Choose some keywords (sidebar → Fetch & Save) to visualize.")

