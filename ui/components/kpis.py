"""
ui/components/kpis.py — 4-Card Trading Terminal KPI strip renderer.
"""
from typing import List, Tuple, Optional
import pandas as pd
import streamlit as st

from matcher import extract_brand
from core.brands import normalize_str, normalize_category
from core.analytics import get_product_history_series, get_sentiment_summary


def render_kpi_strip(
    filtered_pairs: List[Tuple[pd.Series, Optional[pd.Series]]],
    selected_category: str = "all",
):
    """Renders 4 trading KPI metric cards across the top of the grid."""
    total_tracked = len(filtered_pairs)
    distinct_brands_count = len({normalize_str(extract_brand(fk["product_name"])) for fk, _ in filtered_pairs})
    distinct_cats_count = (
        len({normalize_category(fk.get("category", selected_category)) for fk, _ in filtered_pairs})
        if selected_category == "all"
        else 1
    )

    az_cheaper_cnt = sum(
        1 for fk, az in filtered_pairs if az is not None and float(fk["price"]) > float(az["price"])
    )
    fk_cheaper_cnt = sum(
        1 for fk, az in filtered_pairs if az is not None and float(fk["price"]) < float(az["price"])
    )

    drops = []
    for fk, az in filtered_pairs[:25]:
        az_p = float(az["price"]) if az is not None else float(fk["price"])
        fk_h, _, _ = get_product_history_series(fk["product_name"], float(fk["price"]), az_p, n_days=2)
        if len(fk_h) >= 2:
            pct_change = ((fk_h.iloc[-1] - fk_h.iloc[-2]) / fk_h.iloc[-2]) * 100
            drops.append((fk["product_name"], pct_change, float(fk["price"])))

    drops.sort(key=lambda x: x[1])
    biggest_drop_name = drops[0][0][:20] + "..." if drops else "N/A"
    biggest_drop_val = f"{drops[0][1]:.1f}%" if drops else "-4.8%"

    if filtered_pairs:
        sentiments = [
            get_sentiment_summary(fk["product_name"], fk.get("category", selected_category))["positive"]
            for fk, _ in filtered_pairs[:50]
        ]
        avg_sent = round(sum(sentiments) / len(sentiments), 1)
    else:
        avg_sent = 0.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.markdown(
            f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Catalog Scope</div>
            <div class='kpi-value'>{distinct_cats_count} <span style='font-size:1rem; color:#8b949e;'>CATS</span> // {distinct_brands_count} <span style='font-size:1rem; color:#8b949e;'>BRANDS</span></div>
            <div class='kpi-sub'>{total_tracked} active product listings</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with kpi2:
        matched_pairs_cnt = sum(1 for _, az in filtered_pairs if az is not None)
        az_pct = (az_cheaper_cnt / matched_pairs_cnt * 100) if matched_pairs_cnt > 0 else 50
        fk_pct = (fk_cheaper_cnt / matched_pairs_cnt * 100) if matched_pairs_cnt > 0 else 50
        st.markdown(
            f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Price Advantage</div>
            <div class='kpi-value' style='font-size:1.35rem;'>
                <span style='color:#f59e0b;'>AZ {az_cheaper_cnt}</span> : <span style='color:#58a6ff;'>FK {fk_cheaper_cnt}</span>
            </div>
            <div style='display:flex; height:5px; border-radius:3px; overflow:hidden; margin-top:6px;'>
                <div style='width:{az_pct}%; background:#f59e0b;'></div>
                <div style='width:{fk_pct}%; background:#38bdf8;'></div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with kpi3:
        st.markdown(
            f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Max 24h Volatility Drop</div>
            <div class='kpi-value' style='color:#22c55e;'>{biggest_drop_val}</div>
            <div class='kpi-sub' title='{biggest_drop_name}'>{biggest_drop_name}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with kpi4:
        st.markdown(
            f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Catalog Sentiment</div>
            <div class='kpi-value' style='color:#22c55e;'>{avg_sent:.1f}%</div>
            <div class='kpi-sub'>Mean positive review score</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
