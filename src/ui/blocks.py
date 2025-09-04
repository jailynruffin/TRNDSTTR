import streamlit as st

def stat_card(label: str, value: str, icon: str = "•"):
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:.5rem">
              <div style="font-size:1.1rem">{icon}</div>
              <div>
                <div style="opacity:.75;font-size:.85rem">{label}</div>
                <div style="font-size:1.6rem;font-weight:700;line-height:1.1">{value}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
