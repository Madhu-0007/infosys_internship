"""
core — Domain business logic, schemas, and classification engines.
"""
from core.models import ProductItem, CompetitorPair, ForecastResult, SentimentSummary
from core.brands import normalize_str, normalize_category, canonical_brand_name
from core.appliances import (
    _APPLIANCE_TYPE_RULES,
    get_appliance_type,
    get_department_name,
    extract_generic_specs,
)
from core.analytics import (
    get_product_history_series,
    compute_holt_winters_forecast,
    compute_forecast_accuracy_mape,
    get_best_time_to_buy_recommendation,
    get_sentiment_summary,
    compute_price_drop_feed,
    product_matches_query,
)
from core.data_loader import (
    PRICE_HISTORY_FILE,
    ALL_SUPPORTED_CATEGORIES,
    make_amazon_search_url,
    reset_and_initialize_price_history,
    scrape_and_index_new_product,
    startup_category_audit,
    load_all_market_data,
)

__all__ = [
    "ProductItem",
    "CompetitorPair",
    "ForecastResult",
    "SentimentSummary",
    "normalize_str",
    "normalize_category",
    "canonical_brand_name",
    "_APPLIANCE_TYPE_RULES",
    "get_appliance_type",
    "get_department_name",
    "extract_generic_specs",
    "get_product_history_series",
    "compute_holt_winters_forecast",
    "compute_forecast_accuracy_mape",
    "get_best_time_to_buy_recommendation",
    "get_sentiment_summary",
    "compute_price_drop_feed",
    "product_matches_query",
    "PRICE_HISTORY_FILE",
    "ALL_SUPPORTED_CATEGORIES",
    "make_amazon_search_url",
    "reset_and_initialize_price_history",
    "scrape_and_index_new_product",
    "startup_category_audit",
    "load_all_market_data",
]
