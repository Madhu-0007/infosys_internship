"""
ui/components/controls.py — Global filters, search input, watchlist toggle, and dynamic drill-downs.
"""
from typing import Dict, Set, Tuple, List, Optional
import pandas as pd
import streamlit as st

from matcher import extract_brand
from core.brands import normalize_str, canonical_brand_name
from core.appliances import _APPLIANCE_TYPE_RULES, get_appliance_type

CATEGORY_DISPLAY_MAP: Dict[str, str] = {
    "All Categories": "all",
    "Mobiles": "mobiles",
    "Laptops": "laptops",
    "Home Appliances": "home_appliances",
}


def render_controls_and_drilldown(
    fk_df_all: pd.DataFrame,
) -> Tuple[str, str, str, bool, Set[str], Set[str]]:
    """
    Renders search input, category selector, watchlist checkbox, and dynamic drill-down.
    
    Returns:
        search_query (str)
        selected_category (str)
        selected_cat_label (str)
        show_watchlist_only (bool)
        selected_drilldown_brands (Set[str])
        selected_drilldown_types (Set[str])
    """
    c_search, c_cat, c_watch = st.columns([2.5, 1.8, 1.2])

    with c_search:
        search_query = st.text_input(
            "Search Catalog",
            placeholder="🔍 Search product name, model, or brand...",
            label_visibility="collapsed",
            key="main_search_input",
        ).strip()

    cat_label_list = list(CATEGORY_DISPLAY_MAP.keys())

    with c_cat:
        if "selected_cat_label" not in st.session_state:
            st.session_state["selected_cat_label"] = "All Categories"
        prev_cat = st.session_state["selected_cat_label"]

        selected_cat_label = st.selectbox(
            "Select Category",
            options=cat_label_list,
            index=cat_label_list.index(st.session_state["selected_cat_label"]),
            label_visibility="collapsed",
            key="cat_selectbox",
        )

        if selected_cat_label != prev_cat:
            st.session_state["selected_cat_label"] = selected_cat_label
            st.session_state["selected_product"] = None
            old_cat_slug = CATEGORY_DISPLAY_MAP.get(prev_cat, "all")
            st.session_state.pop(f"drilldown_brands_{old_cat_slug}", None)
            st.session_state.pop(f"drilldown_types_{old_cat_slug}", None)
            st.rerun()

        selected_category = CATEGORY_DISPLAY_MAP[selected_cat_label]

    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = set()

    with c_watch:
        watchlist_count = len(st.session_state["watchlist"])
        show_watchlist_only = st.checkbox(
            f"⭐ Watchlist ({watchlist_count})",
            value=False,
            help="Show only starred products across all categories",
        )

    is_single_category = selected_category != "all"
    selected_drilldown_brands: Set[str] = set()
    selected_drilldown_types: Set[str] = set()

    if is_single_category:
        if selected_category == "home_appliances":
            # Item categories drilldown (AC, Fridge, Washer, etc.)
            present_types = {get_appliance_type(str(p)) for p in fk_df_all["product_name"].dropna()}
            available_appliance_types = [
                label for label, _slug, _kws in _APPLIANCE_TYPE_RULES
                if label in present_types
            ]
            if not available_appliance_types:
                available_appliance_types = [label for label, _slug, _kws in _APPLIANCE_TYPE_RULES if _slug != "other"]

            st.markdown(
                f"<div style='font-size:0.8rem; color:#8b949e; font-family:\"JetBrains Mono\", monospace; margin-top:0.4rem; margin-bottom:0.2rem;'>"
                f"🧺 APPLIANCE CATEGORY DRILL-DOWN ({selected_cat_label.upper()}): Select one or more categories (e.g. AC, Fridge)"
                f"</div>",
                unsafe_allow_html=True,
            )

            chosen_type_labels = st.multiselect(
                "Select Appliance Categories",
                options=available_appliance_types,
                default=[],
                placeholder="Select appliance categories (e.g. AC, Fridge, Washing Machine)...",
                label_visibility="collapsed",
                key=f"drilldown_types_{selected_category}",
            )
            selected_drilldown_types = set(chosen_type_labels)

        else:
            # Brand drilldown (Apple, Samsung, Dell, HP, etc.)
            category_brands_dict = {}
            for p in fk_df_all["product_name"].dropna():
                b_raw = extract_brand(p)
                b_norm = normalize_str(b_raw)
                if b_norm and b_norm not in category_brands_dict:
                    category_brands_dict[b_norm] = canonical_brand_name(b_raw)

            sorted_brand_keys = sorted(category_brands_dict.keys(), key=lambda k: category_brands_dict[k].upper())
            available_brand_names = [category_brands_dict[k] for k in sorted_brand_keys]

            st.markdown(
                f"<div style='font-size:0.8rem; color:#8b949e; font-family:\"JetBrains Mono\", monospace; margin-top:0.4rem; margin-bottom:0.2rem;'>"
                f"🏢 BRAND DRILL-DOWN ({selected_cat_label.upper()}): Select one or more brands"
                f"</div>",
                unsafe_allow_html=True,
            )

            chosen_brand_labels = st.multiselect(
                "Select Brands",
                options=available_brand_names,
                default=[],
                placeholder="Select at least one brand...",
                label_visibility="collapsed",
                key=f"drilldown_brands_{selected_category}",
            )
            selected_drilldown_brands = {normalize_str(b) for b in chosen_brand_labels}

    return (
        search_query,
        selected_category,
        selected_cat_label,
        show_watchlist_only,
        selected_drilldown_brands,
        selected_drilldown_types,
    )
