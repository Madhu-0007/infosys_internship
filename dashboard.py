"""
dashboard.py — Ground-up Dark Trading Terminal E-Commerce Competitor Price Tracker.
Flipkart vs Amazon Direct Intelligence Engine.

Refactored Architecture:
- core/ : Pure business logic, typed domain models, Holt-Winters forecasting, sentiment extraction, and data loaders.
- ui/   : High-performance terminal styles, Plotly charts, topbars, KPI cards, product cards, and detail views.
"""
import datetime
import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from matcher import extract_brand
from core import (
    ProductItem,
    CompetitorPair,
    _APPLIANCE_TYPE_RULES,
    get_appliance_type,
    get_department_name,
    canonical_brand_name,
    normalize_str,
    normalize_category,
    product_matches_query,
    reset_and_initialize_price_history,
    startup_category_audit,
    load_all_market_data,
    scrape_and_index_new_product,
)
from ui import (
    inject_terminal_css,
    render_topbar,
    render_controls_and_drilldown,
    render_kpi_strip,
    render_price_drop_feed,
    render_product_card,
    render_product_detail_view,
    safe_button,
)

logger = logging.getLogger("CompetitorTracker")

# -----------------------------------------------------------------------------
# 1. Page Configuration & Terminal Theme Injection
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="COMP-TERMINAL // Competitor Price Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_terminal_css()


# -----------------------------------------------------------------------------
# 2. Startup Cache & Sanitizers (Run once per server instance)
# -----------------------------------------------------------------------------
@st.cache_resource
def _run_startup_sanitizer():
    """Runs once per server startup to sanitize URLs and clean legacy paths."""
    reset_and_initialize_price_history()
    return True


@st.cache_resource
def _run_startup_audit():
    """Runs once per server startup to audit available categories and brands."""
    return startup_category_audit()


reset_and_initialize_price_history()
_run_startup_audit()





# -----------------------------------------------------------------------------
# 3. Main Dashboard Controller
# -----------------------------------------------------------------------------
def main():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Top Status Bar
    render_topbar(now_str)

    # Initial data load for global controls
    if "selected_cat_label" not in st.session_state:
        st.session_state["selected_cat_label"] = "All Categories"

    category_slug_map = {
        "All Categories": "all",
        "Mobiles": "mobiles",
        "Laptops": "laptops",
        "Home Appliances": "home_appliances",
    }
    current_cat_slug = category_slug_map.get(st.session_state["selected_cat_label"], "all")
    df_for_controls = load_all_market_data(selected_category=current_cat_slug)
    fk_df_all = df_for_controls[df_for_controls["source"] == "flipkart"].copy()

    # Render Controls & Dynamic Drilldown
    (
        search_query,
        selected_category,
        selected_cat_label,
        show_watchlist_only,
        selected_drilldown_brands,
        selected_drilldown_types,
    ) = render_controls_and_drilldown(fk_df_all)

    is_single_category = selected_category != "all"

    # Active dataset and Amazon pairing
    df_global = load_all_market_data(selected_category="all")
    fk_df_global = df_global[df_global["source"] == "flipkart"].copy()
    az_df_global = df_global[df_global["source"] == "amazon"].copy()

    df_cat = load_all_market_data(selected_category=selected_category)
    fk_df_cat = df_cat[df_cat["source"] == "flipkart"].copy()
    az_df_cat = df_cat[df_cat["source"] == "amazon"].copy()

    searched_cross_category = False
    if search_query:
        cat_matches = [
            r for _, r in fk_df_cat.iterrows()
            if product_matches_query(
                r["product_name"],
                extract_brand(r["product_name"]),
                normalize_str(extract_brand(r["product_name"])),
                r.get("category", selected_category),
                search_query,
            )
        ]
        if is_single_category and not cat_matches:
            active_fk_df = fk_df_global
            active_az_df = az_df_global
            searched_cross_category = True
        else:
            active_fk_df = fk_df_cat
            active_az_df = az_df_cat
    else:
        active_fk_df = fk_df_cat
        active_az_df = az_df_cat

    # Prompt user if single category is selected without selecting any drilldown item
    if is_single_category and not search_query:
        if selected_category == "home_appliances" and not selected_drilldown_types:
            st.info(f"👉 Select at least one appliance category (e.g. AC, Fridge, Washing Machine) from the drill-down above to view {selected_cat_label} products.")
            return
        elif selected_category != "home_appliances" and not selected_drilldown_brands:
            st.info(f"👉 Select at least one brand from the brand drill-down above to view {selected_cat_label} products.")
            return

    # Filter product pairs
    filtered_pairs: List[Tuple[pd.Series, Optional[pd.Series]]] = []
    for _, fk_row in active_fk_df.iterrows():
        p_name = fk_row["product_name"]
        b_raw = extract_brand(p_name)
        b_norm = normalize_str(b_raw)
        row_cat = fk_row.get("category", selected_category)

        if show_watchlist_only and p_name not in st.session_state["watchlist"]:
            continue

        if not search_query and is_single_category:
            if selected_category == "home_appliances":
                if selected_drilldown_types:
                    p_atype = get_appliance_type(p_name)
                    if p_atype not in selected_drilldown_types:
                        continue
            else:
                if selected_drilldown_brands and (b_norm not in selected_drilldown_brands):
                    continue

        if search_query:
            if not product_matches_query(p_name, b_raw, b_norm, row_cat, search_query):
                continue

        m_id = fk_row.get("matched_id")
        az_match = active_az_df[active_az_df["matched_id"] == m_id] if m_id and pd.notna(m_id) else pd.DataFrame()
        if az_match.empty:
            az_match = active_az_df[active_az_df["product_name"] == p_name]

        az_row = az_match.iloc[0] if not az_match.empty else None
        filtered_pairs.append((fk_row, az_row))

    # Detail View Check
    if "selected_product" not in st.session_state:
        st.session_state["selected_product"] = None

    prev_search = st.session_state.get("_prev_search_query", "")
    if search_query != prev_search:
        if st.session_state.get("selected_product") and search_query:
            st.session_state["selected_product"] = None
        st.session_state["_prev_search_query"] = search_query

    if st.session_state["selected_product"]:
        sel_name = st.session_state["selected_product"]
        sel_pair = next((pair for pair in filtered_pairs if pair[0]["product_name"] == sel_name), None)
        if sel_pair:
            render_product_detail_view(sel_name, sel_pair[0], sel_pair[1], selected_category)
            return

    # Render Trading KPIs Strip
    render_kpi_strip(filtered_pairs, selected_category)

    # Render Price Drop Feed
    render_price_drop_feed(filtered_pairs, selected_category)

    # Cross-Category Match Notification
    if searched_cross_category and filtered_pairs:
        st.info(f"💡 No direct matches found within '{selected_cat_label}', but found {len(filtered_pairs)} matching products across other departments:")

    # Empty State & On-Demand Live Indexer
    if not filtered_pairs:
        if search_query:
            auto_key = f"auto_scraped_{normalize_str(search_query)}"
            if not st.session_state.get(auto_key, False):
                _known_brands = {
                    "apple", "samsung", "xiaomi", "redmi", "realme", "oneplus", "vivo",
                    "oppo", "poco", "motorola", "nokia", "iqoo", "nothing", "cmf",
                    "honor", "infinix", "google", "pixel", "lg", "hp", "dell", "lenovo",
                    "asus", "acer", "msi", "sony", "whirlpool", "bosch", "ifb", "voltas",
                    "daikin", "godrej", "haier", "hitachi", "panasonic", "carrier",
                    "philips", "havells", "bajaj", "crompton", "usha", "kent", "aquaguard",
                    "iphone", "galaxy", "macbook", "ipad",
                }
                _product_kws = {
                    "phone", "mobile", "smartphone", "laptop", "tablet", "tv", "ac",
                    "fridge", "washing", "microwave", "purifier", "geyser", "fan",
                    "camera", "earphone", "headphone", "watch", "speaker", "router",
                    "monitor", "keyboard", "mouse", "printer", "projector", "vacuum",
                    "refrigerator", "dishwasher", "oven", "cooler", "heater", "blender",
                    "gb", "tb", "ram", "ssd", "hdd", "5g", "4g", "pro", "max", "ultra",
                    "plus", "lite", "mini", "gen", "series", "edition", "inch", "hz",
                    "inverter", "ton", "door", "star", "rpm", "litre", "watt",
                }
                sq_tokens = set(normalize_str(search_query).split())
                is_meaningful = (
                    len(sq_tokens) >= 2
                    or bool(sq_tokens & _known_brands)
                    or bool(sq_tokens & _product_kws)
                )

                if is_meaningful:
                    st.session_state[auto_key] = True
                    with st.spinner(f'🔍 "{search_query}" not in catalog — estimating prices from market data...'):
                        success, product_name = scrape_and_index_new_product(search_query, selected_category)
                        if success:
                            st.toast(f'✅ Indexed "{product_name}" with estimated market pricing', icon="🚀")
                            st.cache_data.clear()
                            st.rerun()
                else:
                    st.session_state[auto_key] = True

            st.markdown(
                f"""
            <div style='background:#161b22; border:1px dashed #f59e0b; border-radius:8px; padding:1.6rem; text-align:center; margin:1.5rem 0;'>
                <div style='font-size:1.8rem; margin-bottom:0.4rem;'>⚡</div>
                <div class='mono' style='font-size:1.15rem; font-weight:800; color:#f0f6fc; margin-bottom:0.4rem;'>
                    NO TRACKED LISTINGS FOUND FOR: "{search_query}"
                </div>
                <div style='font-size:0.86rem; color:#8b949e; max-width:620px; margin:0 auto 1.2rem auto; line-height:1.4;'>
                    Live scraping did not find verified dual-platform matches for this search query.
                    Try searching with specific brand or model keywords.
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            col_sc1, col_sc2, col_sc3 = st.columns([1, 1.8, 1])
            with col_sc2:
                if safe_button(
                    f"🔄 Force Re-Scrape \"{search_query}\" Across Flipkart & Amazon",
                    key="btn_force_rescrape",
                    stretch=True,
                ):
                    st.session_state[auto_key] = False
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.info("No products match the selected criteria.")
        return

    # Grouping Strategy:
    # - Home Appliances -> Group by Appliance Category (AC, Fridge, etc.)
    # - Gadgets / Consumer Electronics -> Group by Brand (Apple, Samsung, etc.)
    is_appliance_view = (
        selected_category == "home_appliances"
        or (
            selected_category == "all"
            and all(
                normalize_category(fk.get("category", "")) == "home_appliances"
                for fk, _ in filtered_pairs
            )
        )
    )

    if is_appliance_view:
        appliance_groups: Dict[str, List[Tuple[pd.Series, Optional[pd.Series]]]] = {}
        for label, _slug, _kws in _APPLIANCE_TYPE_RULES:
            appliance_groups[label] = []

        for fk_row, az_row in filtered_pairs:
            atype = get_appliance_type(str(fk_row.get("product_name", "")))
            appliance_groups.setdefault(atype, []).append((fk_row, az_row))

        global_card_counter = 0
        for atype_label, pairs in appliance_groups.items():
            if not pairs:
                continue

            pairs.sort(key=lambda p: (
                canonical_brand_name(extract_brand(str(p[0].get("product_name", "")))).upper(),
                str(p[0].get("product_name", "")).lower(),
            ))
            total_in_type = len(pairs)
            st.markdown(
                f"""
            <div class='department-banner' style='margin-top:1.2rem;'>
                {atype_label}
                <span style='font-size:0.8rem; color:#8b949e; margin-left:0.5rem;'>({total_in_type} products)</span>
            </div>""",
                unsafe_allow_html=True,
            )
            cols_per_row = 3
            for i in range(0, len(pairs), cols_per_row):
                row_items = pairs[i: i + cols_per_row]
                cols = st.columns(cols_per_row)
                for c_idx, (fk_row, az_row) in enumerate(row_items):
                    with cols[c_idx]:
                        render_product_card(
                            fk_row,
                            az_row,
                            fk_row.get("category", selected_category),
                            card_index=global_card_counter,
                        )
                        global_card_counter += 1

    else:
        departments: Dict[str, Dict[str, List[Tuple[pd.Series, Optional[pd.Series]]]]] = {}
        for fk_row, az_row in filtered_pairs:
            row_cat = fk_row.get("category", selected_category)
            dept_name = get_department_name(row_cat)
            b_raw = extract_brand(str(fk_row.get("product_name", "")))
            comp_name = canonical_brand_name(b_raw)
            departments.setdefault(dept_name, {}).setdefault(comp_name, []).append((fk_row, az_row))

        sorted_dept_names = sorted(departments.keys())
        global_card_counter = 0

        for dept in sorted_dept_names:
            comp_dict = departments[dept]
            if not is_single_category:
                total_dept_items = sum(len(pairs) for pairs in comp_dict.values())
                st.markdown(
                    f"<div class='department-banner'>{dept} <span style='font-size:0.8rem; color:#8b949e;'>({total_dept_items} products)</span></div>",
                    unsafe_allow_html=True,
                )

            for comp in sorted(comp_dict.keys(), key=lambda c: c.upper()):
                comp_pairs = comp_dict[comp]
                comp_pairs.sort(key=lambda p: str(p[0].get("product_name", "")).strip().lower())

                st.markdown(
                    f"""
                <div class='brand-group-header'>
                    <div class='brand-group-title'>🏢 {comp}</div>
                    <div class='brand-count-badge'>{len(comp_pairs)} products</div>
                </div>""",
                    unsafe_allow_html=True,
                )

                cols_per_row = 3
                for i in range(0, len(comp_pairs), cols_per_row):
                    row_items = comp_pairs[i: i + cols_per_row]
                    cols = st.columns(cols_per_row)
                    for c_idx, (fk_row, az_row) in enumerate(row_items):
                        with cols[c_idx]:
                            render_product_card(
                                fk_row,
                                az_row,
                                fk_row.get("category", selected_category),
                                card_index=global_card_counter,
                            )
                            global_card_counter += 1


if __name__ == "__main__":
    main()