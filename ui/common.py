"""
ui/common.py — Streamlit UI helper utilities and backwards-compatible wrappers.
"""
from typing import Optional, Dict
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_plotly_chart(
    fig: go.Figure, key: Optional[str] = None, config: Optional[Dict] = None
):
    """Safely renders Plotly chart using width='stretch' to eliminate deprecation warnings."""
    cfg = config or {"displayModeBar": False}
    try:
        st.plotly_chart(fig, config=cfg, width="stretch", key=key)
    except TypeError:
        st.plotly_chart(fig, config=cfg, use_container_width=True, key=key)


def safe_button(label: str, key: Optional[str] = None, stretch: bool = True) -> bool:
    """Renders button using width='stretch' to eliminate deprecation warnings."""
    try:
        return st.button(label, key=key, width="stretch" if stretch else "content")
    except TypeError:
        return st.button(label, key=key, use_container_width=stretch)


def safe_dataframe(df: pd.DataFrame, hide_index: bool = True, stretch: bool = True):
    """Renders DataFrame using width='stretch' to eliminate deprecation warnings."""
    try:
        st.dataframe(df, hide_index=hide_index, width="stretch" if stretch else "content")
    except TypeError:
        st.dataframe(df, hide_index=hide_index, use_container_width=stretch)
