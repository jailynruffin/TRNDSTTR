# src/ui/sections.py
import streamlit as st
from .. import analytics
from .charts import line_interest_altair, movers_with_focus

def picker(key: str = "picker_main") -> list[str]:
    with st.container(border=True):
        st.subheader("Interest over time (from database)")
        return st.multiselect(
            "Select keywords to visualize",
            options=[],
            default=[],
            key=key,   # <-- unique per call
        )

def key_metrics(filter_keywords: list[str] | None = None):
    kpi = analytics.kpis(filter_keywords, last_days=7)
    if kpi is None or kpi.empty:
        st.info("No data yet — fetch some keywords in the sidebar.")
        return None

    with st.container(border=True):
        st.subheader("Key Metrics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Keywords tracked", f"{kpi['keyword'].nunique()}")
        c2.metric("Total interest (7d avg sum)", f"{int(kpi['avg7'].sum())}")
        top = kpi.sort_values("delta", ascending=False).head(1)
        if not top.empty:
            c3.metric("Top mover (Δ last 7d)", top.iloc[0]["keyword"], f"{int(top.iloc[0]['delta'])}")

    with st.container(border=True):
        st.subheader("Top Movers (last 7 days vs previous 7)")
        show = kpi.sort_values("delta", ascending=False).head(10)[
            ["keyword", "avg7", "avg_prev7", "delta", "pct_change"]
        ]
        csv_kpi = show.to_csv(index=False).encode("utf-8")
        st.download_button("Download Top Movers (CSV)", data=csv_kpi,
                           file_name="top_movers.csv", mime="text/csv")
        st.dataframe(show, use_container_width=True)

        kw_list = kpi["keyword"].tolist()
        ts_df = analytics.timeseries_for(kw_list)
        movers_with_focus(kpi, ts_df)

    return kpi

def timeseries(keywords: list[str]):
    import io
    import pandas as pd

    df = analytics.timeseries_for(keywords)
    if df is None or df.empty:
        st.info("No rows yet—click Fetch & Save in the sidebar.")
        return None

    with st.container(border=True):
        st.subheader("Interest over time")
        line_interest_altair(df)

        csv_ts = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Timeseries (CSV)", data=csv_ts,
                           file_name="timeseries.csv", mime="text/csv")

        pivot = (
            df.groupby(["date_ts", "keyword"], as_index=False)["interest"]
              .mean()
              .pivot(index="date_ts", columns="keyword", values="interest")
              .sort_index()
        )
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="timeseries_long")
            pivot.to_excel(writer, sheet_name="timeseries_pivot")
        buf.seek(0)
        st.download_button("Download Timeseries (Excel)", data=buf,
                           file_name="timeseries.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.caption(f"{len(df)} rows • {len(keywords)} keywords")

    return df

