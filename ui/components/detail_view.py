"""
ui/components/detail_view.py — Comprehensive terminal asset inspection view.
"""
from typing import Optional
import pandas as pd
import streamlit as st

from matcher import extract_brand
from core.brands import canonical_brand_name
from core.analytics import (
    get_product_history_series,
    compute_holt_winters_forecast,
    compute_forecast_accuracy_mape,
    get_best_time_to_buy_recommendation,
    get_sentiment_summary,
)
from core.data_loader import make_amazon_search_url
from ui.common import safe_dataframe, render_plotly_chart
from ui.charts import render_divergence_chart, render_sentiment_donut


def render_product_detail_view(
    product_name: str,
    item_fk: pd.Series,
    item_az: Optional[pd.Series],
    category: str,
):
    """Renders comprehensive terminal asset analysis for a selected product."""
    if st.button("← Return to Market Grid", key="btn_back_grid"):
        st.session_state["selected_product"] = None
        st.rerun()

    fk_price = float(item_fk.get("price", 0))
    fk_url = str(item_fk.get("url", "")).strip()
    has_az = item_az is not None and not pd.isna(item_az.get("price"))
    az_price = float(item_az.get("price", fk_price)) if has_az else fk_price
    az_url = str(item_az.get("url", "")).strip() if has_az else ""
    brand = canonical_brand_name(extract_brand(product_name))

    diff = fk_price - az_price if has_az else 0
    abs_diff = abs(diff)
    cheaper_store = "Amazon" if diff > 0 else "Flipkart" if diff < 0 else "Tie"
    higher_price = max(fk_price, az_price)
    pct_diff = (abs_diff / higher_price * 100) if higher_price > 0 else 0

    st.markdown(
        f"""
    <div style='margin-bottom:1rem; border-bottom:1px solid #30363d; padding-bottom:0.75rem;'>
        <div style='font-size:0.78rem; color:#8b949e; font-family:"JetBrains Mono", monospace;'>TERMINAL // ASSET INSPECTION // {brand.upper()}</div>
        <h2 style='margin:0.2rem 0; font-size:1.6rem;'>{product_name}</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 1. Arbitrage Savings Calculator
    if has_az and abs_diff > 0:
        other_store = "Flipkart" if cheaper_store == "Amazon" else "Amazon"
        st.markdown(
            f"""
        <div class='savings-banner'>
            <div class='savings-title'>⚡ ARBITRAGE SAVINGS CALCULATOR</div>
            <div class='savings-amount'>Save ₹{abs_diff:,.0f} ({pct_diff:.1f}%)</div>
            <div style='font-size:0.95rem; color:#e6edf3;'>
                Procuring via <b>{cheaper_store}</b> yields an immediate net saving of 
                <span class='mono' style='font-weight:700; color:#22c55e;'>₹{abs_diff:,.0f}</span> compared to {other_store}.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # 2. Historical Divergence & Forecast Chart
    fk_hist, az_hist, dates = get_product_history_series(product_name, fk_price, az_price, n_days=30)
    fc_fk = compute_holt_winters_forecast(fk_hist, horizon_days=7)
    fc_az = compute_holt_winters_forecast(az_hist, horizon_days=7)

    st.markdown("### 📈 Price History & Holt-Winters 7-Day Forecast Extension")
    fig_diverge = render_divergence_chart(
        fk_hist=fk_hist,
        az_hist=az_hist,
        dates=dates,
        fc_fk=fc_fk,
        fc_az=fc_az,
        has_az=has_az,
        diff=diff,
        cheaper_store=cheaper_store,
    )
    render_plotly_chart(fig_diverge, key="chart_diverge_detail", config={"displayModeBar": True})

    # 3. Best-Time-To-Buy Indicator (Heuristic)
    active_hist = az_hist if (has_az and diff > 0) else fk_hist
    active_trend = fc_az["trend"] if (has_az and diff > 0) else fc_fk["trend"]
    rec = get_best_time_to_buy_recommendation(
        az_price if (has_az and diff > 0) else fk_price, active_hist, active_trend
    )

    st.markdown(
        f"""
    <div class='recommendation-box'>
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem;'>
            <span style='font-family:"JetBrains Mono", monospace; font-size:0.78rem; color:#8b949e; text-transform:uppercase;'>
                🎯 Best-Time-To-Buy Heuristic
            </span>
            <span style='background:{rec["badge_color"]}; color:#0d1117; font-weight:800; font-size:0.75rem; padding:2px 8px; border-radius:4px; font-family:"JetBrains Mono", monospace;'>
                {rec["verdict"]}
            </span>
        </div>
        <div style='font-size:0.92rem; color:#f0f6fc;'>{rec["explanation"]}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 4. Price Snapshot Table & Direct Checkout Links
    st.markdown("### 📊 Price Timeline Snapshot & Direct Links")
    p7_fk = fk_hist.iloc[-7]
    p30_fk = fk_hist.iloc[0]

    snapshot_rows = [
        {
            "Platform": "🛒 Flipkart",
            "30 Days Ago": f"₹{p30_fk:,.0f}",
            "7 Days Ago": f"₹{p7_fk:,.0f}",
            "Current Price": f"₹{fk_price:,.0f}",
            "7D Predicted": f"₹{fc_fk['predicted_7d']:,.0f}",
            "Forecast Confidence": f"{fc_fk['confidence']} CONFIDENCE",
        }
    ]

    if has_az:
        p7_az = az_hist.iloc[-7]
        p30_az = az_hist.iloc[0]
        snapshot_rows.append(
            {
                "Platform": "📦 Amazon",
                "30 Days Ago": f"₹{p30_az:,.0f}",
                "7 Days Ago": f"₹{p7_az:,.0f}",
                "Current Price": f"₹{az_price:,.0f}",
                "7D Predicted": f"₹{fc_az['predicted_7d']:,.0f}",
                "Forecast Confidence": f"{fc_az['confidence']} CONFIDENCE",
            }
        )

    safe_dataframe(pd.DataFrame(snapshot_rows), hide_index=True, stretch=True)

    # Direct Checkout Links
    detail_links = []
    if fk_url and fk_url.startswith("http"):
        detail_links.append(f"<a href='{fk_url}' target='_blank' class='link-btn'>🛒 Buy on Flipkart (₹{fk_price:,.0f}) ↗</a>")
    if has_az and az_url and az_url.startswith("http"):
        direct_az_url = make_amazon_search_url(product_name, az_url)
        detail_links.append(f"<a href='{direct_az_url}' target='_blank' class='link-btn'>📦 Buy on Amazon (₹{az_price:,.0f}) ↗</a>")

    if detail_links:
        st.markdown(f"<div style='margin:0.8rem 0;'>{''.join(detail_links)}</div>", unsafe_allow_html=True)

    # 5. Forecast Accuracy Tracking (MAPE)
    mape_val = compute_forecast_accuracy_mape(active_hist)
    c_acc1, _c_acc2 = st.columns([1, 1])
    with c_acc1:
        if mape_val is not None:
            accuracy_score = max(0.0, round(100.0 - mape_val, 1))
            st.markdown(
                f"""
            <div class='kpi-card' style='padding:0.75rem 1rem;'>
                <div class='kpi-label'>Holt-Winters Tracking Accuracy (MAPE)</div>
                <div class='mono' style='font-size:1.25rem; font-weight:800; color:#22c55e;'>
                    {accuracy_score}% Accuracy <span style='font-size:0.8rem; color:#8b949e;'>(MAPE: {mape_val}%)</span>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
            <div class='kpi-card' style='padding:0.75rem 1rem;'>
                <div class='kpi-label'>Forecast Accuracy (MAPE)</div>
                <div style='font-size:0.88rem; color:#8b949e;'>Not enough historical data points yet</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # 6. Sentiment Breakdown & Snippets
    st.markdown("### 💬 Review Sentiment Intelligence (OpenAI Engine)")
    sent_data = get_sentiment_summary(product_name, category)
    col_donut, col_snip_fk, col_snip_az = st.columns([1.2, 1.4, 1.4])

    with col_donut:
        fig_donut = render_sentiment_donut(
            sent_data["positive"], sent_data["neutral"], sent_data["negative"]
        )
        render_plotly_chart(fig_donut, key="chart_sentiment_donut")

    with col_snip_fk:
        st.markdown("#### 🛒 Flipkart Reviews")
        for snip in sent_data["fk_snippets"]:
            st.markdown(
                f"<div style='background:#0d1117; border-left:3px solid #38bdf8; padding:0.4rem 0.6rem; border-radius:4px; margin-bottom:6px; font-size:0.8rem;'>\"{snip}\"</div>",
                unsafe_allow_html=True,
            )

    with col_snip_az:
        st.markdown("#### 📦 Amazon Reviews")
        for snip in sent_data["az_snippets"]:
            st.markdown(
                f"<div style='background:#0d1117; border-left:3px solid #f59e0b; padding:0.4rem 0.6rem; border-radius:4px; margin-bottom:6px; font-size:0.8rem;'>\"{snip}\"</div>",
                unsafe_allow_html=True,
            )
