# src/ui/charts.py
import altair as alt
import pandas as pd
import streamlit as st

def _altair_defaults():
    alt.themes.enable('none')
    alt.data_transformers.disable_max_rows()
    alt.renderers.set_embed_options(actions=False)
    return {
        "config": {
            "axis": {"labelFontSize": 12, "titleFontSize": 12},
            "legend": {"labelFontSize": 12, "titleFontSize": 12, "orient": "bottom"},
            "view": {"stroke": "transparent"}
        }
    }

# inside movers_with_focus(...) before building charts:
alt.themes.register('trnd', lambda: _altair_defaults())
alt.themes.enable('trnd')


def line_interest_altair(df: pd.DataFrame, title: str = "Interest over time"):
    _ = _altair_defaults()
    df = df.groupby(["date_ts", "keyword"], as_index=False)["interest"].mean()
    chart = (
        alt.Chart(df, title=title)
        .mark_line()
        .encode(
            x=alt.X("date_ts:T", title="Date"),
            y=alt.Y("interest:Q", title="Interest"),
            color=alt.Color("keyword:N", legend=alt.Legend(orient="bottom")),
            tooltip=[alt.Tooltip("date_ts:T"), alt.Tooltip("keyword:N"), alt.Tooltip("interest:Q")]
        )
        .properties(height=380)
    )
    st.altair_chart(chart, use_container_width=True)


def movers_with_focus(kpi_df: pd.DataFrame, timeseries_df: pd.DataFrame | None):
    """
    Interactive Top Movers:
      - Horizontal bar chart (avg7) with click selection
      - Linked line chart below filtered to selected keyword(s)
    """
    if kpi_df is None or kpi_df.empty:
        st.info("No KPI data to visualize.")
        return

    kpi = kpi_df[["keyword", "avg7", "avg_prev7", "delta", "pct_change"]].copy()

    select_kw = alt.selection_point(fields=["keyword"], on="click", clear="true")

    bars = (
        alt.Chart(kpi, title="Top Movers (last 7 days vs previous 7)")
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            y=alt.Y("keyword:N", sort="-x", title=""),
            x=alt.X("avg7:Q", title="7-day avg interest"),
            color=alt.condition(select_kw, alt.value("#1f77b4"), alt.value("#cbd5e1")),
            tooltip=[
                alt.Tooltip("keyword:N", title="keyword"),
                alt.Tooltip("avg7:Q", title="avg7", format=".2f"),
                alt.Tooltip("avg_prev7:Q", title="avg_prev7", format=".2f"),
                alt.Tooltip("delta:Q", title="Δ", format=".2f"),
                alt.Tooltip("pct_change:Q", title="% change", format=".1f"),
            ],
        )
        .add_params(select_kw)
        .properties(height=220)
    )

    if timeseries_df is not None and not timeseries_df.empty:
        ts = timeseries_df.groupby(["date_ts", "keyword"], as_index=False)["interest"].mean()
        line = (
            alt.Chart(ts, title="Interest over time (selected)")
            .mark_line()
            .encode(
                x=alt.X("date_ts:T", title="Date"),
                y=alt.Y("interest:Q", title="Interest"),
                color=alt.Color("keyword:N", legend=alt.Legend(title="Keyword")),
                tooltip=[
                    alt.Tooltip("date_ts:T", title="Date"),
                    alt.Tooltip("keyword:N", title="Keyword"),
                    alt.Tooltip("interest:Q", title="Interest"),
                ],
            )
            .transform_filter(select_kw)
            .properties(height=320)
        )
        chart = (bars & line).resolve_scale(color="independent")
    else:
        chart = bars

    st.altair_chart(chart, use_container_width=True)
