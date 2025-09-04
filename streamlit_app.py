import streamlit as st
from pathlib import Path
from src.ui.blocks import stat_card
from src.ui.sidebar import render_fetch_controls
from src.ui.sections import picker, key_metrics, timeseries
from src.analytics import distinct_keywords
from src.ui.header import header

st.set_page_config(page_title="TRNDSTTR", page_icon="📈", layout="wide")

def _load_css():
    try:
        css = Path("styles/ui.css").read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception:
        pass

_load_css()          
header()             

# Chips 
tf = st.session_state.get("last_timeframe", "today 3-m")
rg = st.session_state.get("last_region", "US")

# ----- Hero stat row -----
left, mid, right = st.columns(3)
with left:
    stat_card("Keywords tracked", str(st.session_state.get("kpi_keywords", 0)), "🔎")
with mid:
    stat_card("Total interest (7d sum)", str(st.session_state.get("kpi_sum", 0)), "⚡")
with right:
    stat_card("Top mover", st.session_state.get("kpi_top", "—"), "📈")

with st.sidebar:
    render_fetch_controls()
    
# ----- Tabs -----
tab_overview, tab_trends = st.tabs(["Overview", "Trends"])

with tab_overview:
    chosen = picker(key="picker_overview")
    active_keywords = chosen or st.session_state.get("last_fetch_keywords", [])
    if not active_keywords:
        try:
            opts = distinct_keywords()
            if opts: active_keywords = opts[:3]
        except Exception:
            active_keywords = []

    # KPIs + Top Movers (also updates the hero values in session_state)
    kpi = key_metrics(filter_keywords=active_keywords)
    if kpi is not None and not kpi.empty:
        st.session_state["kpi_keywords"] = kpi["keyword"].nunique()
        st.session_state["kpi_sum"] = int(kpi["avg7"].sum())
        top = kpi.sort_values("delta", ascending=False).head(1)
        st.session_state["kpi_top"] = top.iloc[0]["keyword"] if not top.empty else "—"

with tab_trends:
    if st.session_state.get("kpi_keywords", 0) == 0:
        st.info("Fetch some keywords in the sidebar to see the trend lines.")
    else:
        timeseries(st.session_state.get("last_fetch_keywords", active_keywords))

# ----- Footer -----
st.markdown(
    """
    <hr style="margin-top:2rem;opacity:.15">
    <div style="display:flex;justify-content:space-between;opacity:.7;font-size:.85rem">
      <span>© TRNDSTTR</span>
      <span>Built by Jailyn Ruffin</span>
    </div>
    """,
    unsafe_allow_html=True,
)
