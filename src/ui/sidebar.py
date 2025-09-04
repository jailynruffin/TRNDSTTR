# src/ui/sidebar.py
import streamlit as st
from ..fetch_trends import fetch_interest_over_time
from pytrends import exceptions as pt_exc

@st.cache_data(show_spinner=False, ttl=60*60)
def _cached_fetch(tuple_keywords, timeframe, geo):
    kws = list(tuple_keywords)
    return fetch_interest_over_time(kws, timeframe=timeframe, geo=geo)

def render_fetch_controls():
    st.header("Fetch Google Trends")
    default = ["Sabrina Carpenter", "Addison Rae", "Taylor Swift"]
    keywords_input = st.text_input("Keywords (comma-separated)", value=", ".join(default))
    timeframe = st.selectbox("Timeframe", ["now 7-d", "today 3-m", "today 12-m", "today 5-y"], index=1)
    geo = st.selectbox("Region", ["US", ""], index=0)
    st.caption("Tip: Up to 5 keywords per fetch • Results cached for 1 hour.")

    if st.button("Fetch & Save", type="primary"):
        kws = [k.strip() for k in keywords_input.split(",") if k.strip()]
        if not kws:
            st.warning("Add at least one keyword.")
            return
        try:
            with st.spinner("Pulling Google Trends…"):
                df = _cached_fetch(tuple(sorted(kws, key=str.lower)), timeframe, geo)
            if df.empty:
                st.info("No data returned. Try different keywords/timeframe.")
            else:
                # remember last fetch to seed filters
                st.session_state["last_fetch_keywords"] = kws
                st.success(f"Ingested {len(df)} rows. Cached for 1 hour.")
        except pt_exc.TooManyRequestsError:
            st.warning("Google Trends rate limit hit (429). Please wait a minute and try again.")
        except Exception as e:
            st.error(f"Fetch failed: {e}")
