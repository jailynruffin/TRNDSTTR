import streamlit as st
from datetime import datetime

def header(app_title: str = "TRNDSTTR ⭐"):
    # HTML so we can control spacing/line-height precisely
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    st.markdown(
        f"""
        <div class="trnd-header">
          <div class="trnd-left">
            <h1 class="trnd-title">{app_title}</h1>
            <div class="trnd-caption">Media &amp; culture trend intelligence for creators and marketers.</div>
          </div>
          <div class="trnd-right">
            <div class="trnd-updated">Last updated: {ts}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
