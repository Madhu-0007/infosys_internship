"""
ui — Modular Streamlit Trading Terminal Presentation Layer.
"""
from ui.styles import inject_terminal_css
from ui.common import render_plotly_chart, safe_button, safe_dataframe
from ui.charts import (
    render_sparkline_chart,
    render_divergence_chart,
    render_sentiment_donut,
)
from ui.components.topbar import render_topbar
from ui.components.controls import render_controls_and_drilldown, CATEGORY_DISPLAY_MAP
from ui.components.kpis import render_kpi_strip
from ui.components.price_feed import render_price_drop_feed
from ui.components.product_card import render_product_card
from ui.components.detail_view import render_product_detail_view

__all__ = [
    "inject_terminal_css",
    "render_plotly_chart",
    "safe_button",
    "safe_dataframe",
    "render_sparkline_chart",
    "render_divergence_chart",
    "render_sentiment_donut",
    "render_topbar",
    "render_controls_and_drilldown",
    "CATEGORY_DISPLAY_MAP",
    "render_kpi_strip",
    "render_price_drop_feed",
    "render_product_card",
    "render_product_detail_view",
]
