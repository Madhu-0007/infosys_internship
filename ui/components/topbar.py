"""
ui/components/topbar.py — Trading Terminal top header and status bar.
"""
import streamlit as st


def render_topbar(now_str: str):
    """Renders the dark trading terminal header bar with live pulse."""
    st.markdown(
        f"""
    <div class='terminal-topbar'>
        <div class='terminal-title'>
            <span class='terminal-pulse'></span> COMP-TERMINAL // COMPETITOR PRICE INTELLIGENCE
        </div>
        <div class='terminal-status'>
            STATUS: <span style='color:#22c55e; font-weight:700;'>NOMINAL</span> | REFRESH: <span class='mono'>{now_str}</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
