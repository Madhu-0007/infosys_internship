"""
forecasting.py — Real time-series price forecasting per product.

Replaces the old same-day proxy model (LightGBM predicting current price
from discount+rating, which was NOT real forecasting). This module uses
actual historical price data from data/price_history.csv.

Approach:
  - Requires minimum 5 data points before generating a forecast
  - Uses Simple Exponential Smoothing (SES) from statsmodels as baseline
  - Outputs: current_price, predicted_price_7d, trend, confidence

Extension point:
  To swap in Prophet or other models later, replace the `forecast_product()`
  function. The interface is: takes a price Series + dates, returns a dict
  with current_price, predicted_price_7d, trend, confidence.

Usage:
    python forecasting.py --category mobiles
    python forecasting.py --all
"""

import os
import logging
import argparse

import pandas as pd
import numpy as np

# Try importing statsmodels for SES; provide clear error if missing
try:
    from statsmodels.tsa.holtwinters import SimpleExpSmoothing
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    logging.warning(
        "statsmodels not installed — forecasting will use moving average fallback. "
        "Install with: pip install statsmodels"
    )

from config.categories import CATEGORIES

# ------------------------------
# Config
# ------------------------------
MIN_HISTORY_LENGTH = 5  # Minimum data points required for forecasting
FORECAST_HORIZON_DAYS = 7
PRICE_HISTORY_FILE = os.path.join("data", "price_history.csv")
FORECAST_OUTPUT_DIR = "data"

# Confidence thresholds based on history length and volatility
# More history + lower volatility = higher confidence
CONFIDENCE_THRESHOLDS = {
    "high": {"min_points": 15, "max_cv": 0.05},
    "medium": {"min_points": 8, "max_cv": 0.15},
    # Everything else is "low"
}

# ------------------------------
# Logging
# ------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def compute_confidence(n_points, cv):
    """Determine confidence level based on data quality.

    Args:
        n_points: number of historical price observations
        cv: coefficient of variation (std/mean) of prices

    Returns:
        str: 'high', 'medium', or 'low'
    """
    if cv is None or np.isnan(cv):
        return "low"

    for level in ["high", "medium"]:
        thresholds = CONFIDENCE_THRESHOLDS[level]
        if n_points >= thresholds["min_points"] and cv <= thresholds["max_cv"]:
            return level

    return "low"


def determine_trend(prices):
    """Determine price trend direction from recent prices.

    Uses simple linear regression slope on the last N observations.

    Returns:
        str: 'up', 'down', or 'flat'
    """
    if len(prices) < 2:
        return "flat"

    # Use numpy polyfit for a simple linear trend
    x = np.arange(len(prices))
    try:
        slope, _ = np.polyfit(x, prices, 1)
    except (np.linalg.LinAlgError, ValueError):
        return "flat"

    # Threshold: consider "flat" if slope is < 0.5% of mean price per period
    mean_price = np.mean(prices)
    if mean_price == 0:
        return "flat"

    relative_slope = abs(slope) / mean_price
    if relative_slope < 0.005:
        return "flat"
    return "up" if slope > 0 else "down"


def forecast_product(prices, dates):
    """Generate a 7-day price forecast for a single product.

    This is the main forecasting function — the extension point for
    swapping in more sophisticated models (Prophet, ARIMA, etc.)
    when enough historical data accumulates.

    Args:
        prices: pd.Series of historical prices (numeric)
        dates: pd.Series of corresponding timestamps

    Returns:
        dict with keys: current_price, predicted_price_7d, trend,
              confidence. Returns None if insufficient data.
    """
    # Clean data
    valid = prices.dropna()
    if len(valid) < MIN_HISTORY_LENGTH:
        return None

    prices_arr = valid.values.astype(float)
    current_price = prices_arr[-1]
    n_points = len(prices_arr)

    # Coefficient of variation for confidence assessment
    mean_price = np.mean(prices_arr)
    std_price = np.std(prices_arr)
    cv = std_price / mean_price if mean_price > 0 else 0

    # Trend direction
    trend = determine_trend(prices_arr)

    # Forecast using Exponential Smoothing (alpha=0.3)
    if n_points >= 3:
        level = float(prices_arr[0])
        for p in prices_arr[1:]:
            level = 0.3 * float(p) + 0.7 * level
        predicted = level
    else:
        predicted = float(np.mean(prices_arr[-3:])) if n_points > 0 else current_price

    # Adjust prediction slightly based on trend for 7-day horizon
    # (since our data intervals may not be daily)
    if trend == "up" and n_points >= 5:
        # Extrapolate upward slightly
        avg_change = np.mean(np.diff(prices_arr[-5:]))
        predicted = predicted + avg_change * 0.5
    elif trend == "down" and n_points >= 5:
        avg_change = np.mean(np.diff(prices_arr[-5:]))
        predicted = predicted + avg_change * 0.5

    # Ensure predicted price isn't negative
    predicted = max(predicted, 0)

    confidence = compute_confidence(n_points, cv)

    return {
        "current_price": round(current_price, 2),
        "predicted_price_7d": round(predicted, 2),
        "trend": trend,
        "confidence": confidence,
        "n_data_points": n_points,
    }


def forecast_category(category):
    """Run forecasting for all products in a category.

    Returns:
        pd.DataFrame with forecast results, or None.
    """
    if not os.path.exists(PRICE_HISTORY_FILE):
        logging.warning(f"No price history file: {PRICE_HISTORY_FILE}")
        return None

    price_df = pd.read_csv(PRICE_HISTORY_FILE)
    price_df = price_df[price_df["category"] == category].copy()

    if price_df.empty:
        logging.warning(f"[{category}] No price history data.")
        return None

    price_df["price"] = pd.to_numeric(price_df["price"], errors="coerce")
    price_df["scraped_at"] = pd.to_datetime(price_df["scraped_at"], errors="coerce")
    price_df = price_df.sort_values("scraped_at")

    # Optionally filter to top-K products only (if selection has been run)
    top_products_file = os.path.join("data", f"{category}_top_products.csv")
    top_pids = None
    if os.path.exists(top_products_file):
        top_df = pd.read_csv(top_products_file)
        if "productid" in top_df.columns:
            top_pids = set(top_df["productid"].dropna().unique())
            logging.info(
                f"[{category}] Filtering forecasts to {len(top_pids)} top products"
            )

    results = []
    grouped = price_df.groupby("productid")

    for pid, group in grouped:
        # Skip non-top-K products if selection has been run
        if top_pids is not None and pid not in top_pids:
            continue

        product_name = group["product_name"].iloc[-1]
        forecast = forecast_product(group["price"], group["scraped_at"])

        if forecast is None:
            results.append({
                "productid": pid,
                "category": category,
                "product_name": product_name,
                "current_price": group["price"].iloc[-1],
                "predicted_price_7d": None,
                "trend": "insufficient_history",
                "confidence": "none",
                "n_data_points": len(group),
                "status": "insufficient_history",
            })
        else:
            results.append({
                "productid": pid,
                "category": category,
                "product_name": product_name,
                **forecast,
                "status": "ok",
            })

    return pd.DataFrame(results)


def main(category=None, all_categories=False):
    """Run forecasting for one or all categories.

    Saves results to data/{category}_forecasts.csv.
    """
    if all_categories:
        categories = list(CATEGORIES.keys())
    elif category:
        categories = [category]
    else:
        categories = ["mobiles"]

    os.makedirs(FORECAST_OUTPUT_DIR, exist_ok=True)
    all_forecasts = []

    for cat in categories:
        logging.info(f"Forecasting prices for category: {cat}")
        forecast_df = forecast_category(cat)

        if forecast_df is not None and not forecast_df.empty:
            # Save per-category forecast
            output_path = os.path.join(
                FORECAST_OUTPUT_DIR, f"{cat}_forecasts.csv"
            )
            forecast_df.to_csv(output_path, index=False, encoding="utf-8-sig")
            logging.info(f"✅ Saved forecasts: {output_path}")
            all_forecasts.append(forecast_df)

            # Summary
            ok_count = (forecast_df["status"] == "ok").sum()
            insuf_count = (forecast_df["status"] == "insufficient_history").sum()
            logging.info(
                f"[{cat}] {ok_count} products forecasted, "
                f"{insuf_count} need more history"
            )
        else:
            logging.warning(f"[{cat}] No forecasts generated.")

    # Save combined forecasts
    if all_forecasts:
        combined = pd.concat(all_forecasts, ignore_index=True)
        combined.to_csv(
            os.path.join(FORECAST_OUTPUT_DIR, "forecasts.csv"),
            index=False, encoding="utf-8-sig"
        )
        logging.info("✅ Saved combined forecasts: data/forecasts.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Time-series price forecasting"
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        choices=list(CATEGORIES.keys()),
        help="Category to forecast"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        dest="all_categories",
        help="Forecast all configured categories"
    )
    args = parser.parse_args()

    main(category=args.category, all_categories=args.all_categories)
