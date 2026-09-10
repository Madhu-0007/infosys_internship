"""
ui/components/product_card.py — Single product comparison card component.
"""
from typing import Optional
import pandas as pd
import streamlit as st

from matcher import extract_brand
from core.brands import canonical_brand_name, normalize_category
from core.appliances import extract_generic_specs
from core.analytics import (
    get_product_history_series,
    compute_holt_winters_forecast,
    get_sentiment_summary,
)
from core.data_loader import make_amazon_search_url
from ui.common import safe_button, render_plotly_chart
from ui.charts import render_sparkline_chart


def render_product_card(
    item_fk: pd.Series,
    item_az: Optional[pd.Series],
    category: str,
    card_index: int,
):
    """Renders a single matched product card with all visual trading signals."""
    p_name = str(item_fk.get("product_name", "Hardware Model"))
    fk_price = float(item_fk.get("price", 0))
    fk_disc = float(item_fk.get("discount", 0))
    fk_rating = float(item_fk.get("rating", 4.3))
    fk_url = str(item_fk.get("url", "")).strip()
    matched_id = item_fk.get("matched_id", f"M_{card_index:04d}")

    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = set()
    is_starred = p_name in st.session_state["watchlist"]

    has_az = item_az is not None and not pd.isna(item_az.get("price"))
    az_price = float(item_az.get("price", 0)) if has_az else 0.0
    az_disc = float(item_az.get("discount", 0)) if has_az else 0.0
    az_rating = float(item_az.get("rating", 4.2)) if has_az else 0.0
    az_url = str(item_az.get("url", "")).strip() if has_az else ""

    brand_raw = extract_brand(p_name)
    brand = canonical_brand_name(brand_raw)
    specs_dict = extract_generic_specs(p_name, category_hint=category)

    if has_az:
        diff = fk_price - az_price
        abs_diff = abs(diff)
        pct_diff = (abs_diff / max(fk_price, az_price) * 100) if max(fk_price, az_price) > 0 else 0
        if diff > 0:
            edge_text = f"Amazon leads by ₹{abs_diff:,.0f} ({pct_diff:.1f}% cheaper). Superior value."
        elif diff < 0:
            edge_text = f"Flipkart leads by ₹{abs_diff:,.0f} ({pct_diff:.1f}% cheaper). Better price."
        else:
            edge_text = "Exact price parity across platforms."
    else:
        diff = 0
        abs_diff = 0
        pct_diff = 0
        edge_text = "Exclusive listing on Flipkart. No direct Amazon match found."

    az_ref_price = az_price if has_az else fk_price
    fk_hist, az_hist, _ = get_product_history_series(p_name, fk_price, az_ref_price, n_days=14)
    active_series = az_hist if (has_az and diff > 0) else fk_hist
    fc_info = compute_holt_winters_forecast(active_series, horizon_days=7)

    cat_slug = normalize_category(category)
    cat_icon = "🧺" if cat_slug == "home_appliances" else "📱" if cat_slug == "mobiles" else "💻"

    with st.container(border=True):
        c_h1, c_h2 = st.columns([1.8, 1.2])
        with c_h1:
            st.markdown(
                f"<span class='spec-chip' style='color:#58a6ff; font-weight:700;'>{brand}</span> "
                f"<span class='spec-chip'>ID: {matched_id}</span>",
                unsafe_allow_html=True,
            )
        with c_h2:
            star_label = "⭐" if is_starred else "☆"
            c_star, c_badge = st.columns([0.35, 0.65])
            with c_star:
                if st.button(star_label, key=f"star_btn_{card_index}", help="Toggle watchlist"):
                    if is_starred:
                        st.session_state["watchlist"].remove(p_name)
                    else:
                        st.session_state["watchlist"].add(p_name)
                    st.rerun()
            with c_badge:
                if has_az:
                    if diff > 0:
                        st.markdown(
                            f"<div style='text-align:right;'><span class='cheaper-badge'>AZ CHEAPER ₹{abs_diff:,.0f}</span></div>",
                            unsafe_allow_html=True,
                        )
                    elif diff < 0:
                        st.markdown(
                            f"<div style='text-align:right;'><span class='cheaper-badge'>FK CHEAPER ₹{abs_diff:,.0f}</span></div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            "<div style='text-align:right;'><span class='spec-chip' style='color:#f59e0b;'>PARITY</span></div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(
                        "<div style='text-align:right;'><span class='spec-chip' style='color:#8b949e;'>SOLO</span></div>",
                        unsafe_allow_html=True,
                    )

        c_thumb, c_title = st.columns([0.2, 0.8])
        with c_thumb:
            st.markdown(f"<div class='thumbnail-box'>{cat_icon}</div>", unsafe_allow_html=True)
        with c_title:
            display_title = p_name if len(p_name) <= 60 else p_name[:57] + "..."
            st.markdown(
                f"<div style='font-size:0.92rem; font-weight:700; color:#f0f6fc; line-height:1.25;' title='{p_name}'>{display_title}</div>",
                unsafe_allow_html=True,
            )

        if specs_dict:
            chips_html = "".join([f"<span class='spec-chip'><b>{k}:</b> {v}</span>" for k, v in specs_dict.items()])
            st.markdown(f"<div style='margin-top:0.4rem;'>{chips_html}</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

        col_fk, col_az = st.columns(2)
        with col_fk:
            win_class = "price-box-winner" if (has_az and diff < 0) else ""
            st.markdown(
                f"""
            <div class='price-box-fk {win_class}'>
                <div style='font-size:0.68rem; color:#8b949e; font-weight:700;'>🛒 FLIPKART</div>
                <div class='mono' style='font-size:1.1rem; font-weight:800; color:#f0f6fc;'>₹{fk_price:,.0f}</div>
                <div style='font-size:0.7rem; color:#8b949e;'>{fk_disc:.0f}% off | ★ {fk_rating:.1f}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col_az:
            if has_az:
                win_class = "price-box-winner" if diff > 0 else ""
                st.markdown(
                    f"""
                <div class='price-box-az {win_class}'>
                    <div style='font-size:0.68rem; color:#8b949e; font-weight:700;'>📦 AMAZON</div>
                    <div class='mono' style='font-size:1.1rem; font-weight:800; color:#f0f6fc;'>₹{az_price:,.0f}</div>
                    <div style='font-size:0.7rem; color:#8b949e;'>{az_disc:.0f}% off | ★ {az_rating:.1f}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div class='unmatched-box'>🚫 Not matched on Amazon</div>",
                    unsafe_allow_html=True,
                )

        st.markdown(f"<div class='edge-box'><b>EDGE:</b> {edge_text}</div>", unsafe_allow_html=True)

        link_items = []
        if fk_url and fk_url.startswith("http"):
            link_items.append(f"<a href='{fk_url}' target='_blank' rel='noopener noreferrer' class='link-btn'>🛒 View on Flipkart ↗</a>")
        if has_az and az_url and az_url.startswith("http"):
            real_az_url = make_amazon_search_url(p_name, az_url)
            link_items.append(f"<a href='{real_az_url}' target='_blank' rel='noopener noreferrer' class='link-btn'>📦 View on Amazon ↗</a>")

        if link_items:
            st.markdown(f"<div style='margin-bottom:0.4rem;'>{''.join(link_items)}</div>", unsafe_allow_html=True)

        c_spk, c_fc = st.columns([1.3, 1.2])
        with c_spk:
            st.markdown(
                "<div style='font-size:0.66rem; color:#8b949e; margin-bottom:2px;'>14D HISTORY</div>",
                unsafe_allow_html=True,
            )
            spark_fig = render_sparkline_chart(active_series, is_winner=True)
            render_plotly_chart(spark_fig, key=f"spark_{card_index}")

        with c_fc:
            trend_icon = "📉" if fc_info["trend"] == "down" else "📈" if fc_info["trend"] == "up" else "➡️"
            trend_color = "#22c55e" if fc_info["trend"] == "down" else "#ef4444" if fc_info["trend"] == "up" else "#f59e0b"
            conf_class = (
                "confidence-badge-high"
                if fc_info["confidence"] == "HIGH"
                else "confidence-badge-med"
                if fc_info["confidence"] == "MED"
                else "confidence-badge-low"
            )
            st.markdown(
                f"""
            <div style='text-align:right;'>
                <div style='font-size:0.66rem; color:#8b949e;'>7D FORECAST</div>
                <div class='mono' style='font-size:0.92rem; font-weight:800; color:{trend_color};'>
                    {trend_icon} ₹{fc_info['predicted_7d']:,.0f}
                </div>
                <div><span class='{conf_class}'>{fc_info['confidence']} CONF</span></div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        sent_info = get_sentiment_summary(p_name, category)
        st.markdown(
            f"""
        <div style='margin-top:0.35rem;'>
            <div style='display:flex; justify-content:space-between; font-size:0.7rem; color:#8b949e; margin-bottom:3px;'>
                <span>Sentiment</span>
                <span class='mono' style='color:#22c55e; font-weight:700;'>{sent_info['positive']}% POSITIVE</span>
            </div>
            <div style='display:flex; height:5px; border-radius:3px; overflow:hidden; background:#21262d;'>
                <div style='width:{sent_info['positive']}%; background:#22c55e;'></div>
                <div style='width:{sent_info['neutral']}%; background:#8b949e;'></div>
                <div style='width:{sent_info['negative']}%; background:#ef4444;'></div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        if safe_button("Inspect Terminal Detail ↗", key=f"btn_inspect_{card_index}", stretch=True):
            st.session_state["selected_product"] = p_name
            st.rerun()
