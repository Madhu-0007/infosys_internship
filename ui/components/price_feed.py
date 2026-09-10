"""
ui/components/price_feed.py — Notable price drop chronological feed component.
"""
from typing import List, Tuple, Optional
import pandas as pd
import streamlit as st

from core.analytics import compute_price_drop_feed


def render_price_drop_feed(
    filtered_pairs: List[Tuple[pd.Series, Optional[pd.Series]]],
    selected_category: str = "all",
):
    """Renders chronological feed of recent high-delta price cuts."""
    with st.expander("📉 Recent Notable Price Drops (Chronological Feed)", expanded=False):
        drop_events = compute_price_drop_feed(filtered_pairs, selected_category)
        if drop_events:
            for ev in drop_events:
                plat_color = "#f59e0b" if ev["platform"] == "Amazon" else "#58a6ff"
                st.markdown(
                    f"<div style='background:#161b22; border:1px solid #30363d; border-radius:6px; padding:0.45rem 0.8rem; margin-bottom:5px; font-size:0.82rem;'>"
                    f"<span class='mono' style='color:#8b949e;'>{ev['date']}</span> — "
                    f"<b style='color:{plat_color};'>{ev['platform']}</b> dropped <b>{ev['product']}</b> by "
                    f"<span class='mono' style='color:#22c55e; font-weight:700;'>{ev['drop']}</span> (now {ev['price']})"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No significant price drops detected in the current catalog view.")
