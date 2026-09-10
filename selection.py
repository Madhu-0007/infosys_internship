"""
selection.py — Product selection and scoring for competitor intelligence.

Computes a composite score per product per category based on:
  - review_count: number of reviews (popularity signal)
  - price_volatility: std(price) / mean(price) from price history
    (indicates price competition / deal activity)

Selects top-K products per category for deep tracking
(reviews + forecasting). Products not in top-K still get price-only
snapshots — this is a cost/relevance filter for expensive operations.

Usage:
    python selection.py --category mobiles
    python selection.py --all
"""

import os
import logging
import argparse

import pandas as pd
import numpy as np

from config.categories import CATEGORIES

# ------------------------------
# Configurable constants
# ------------------------------
# Weights for composite score (must sum to 1.0)
WEIGHT_REVIEWS = 0.4
WEIGHT_VOLATILITY = 0.6

# Minimum number of price history data points before volatility
# is considered meaningful. Below this, we rank by review_count only.
MIN_HISTORY_POINTS = 3

# Number of top products to select per category for deep tracking (default: 100)
TOP_K = int(os.getenv("TOP_K", "100"))

# File paths
PRICE_HISTORY_FILE = os.path.join("data", "price_history.csv")
REVIEWS_DIR = "data"
SELECTION_OUTPUT_DIR = "data"

# ------------------------------
# Logging
# ------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def normalize_series(s):
    """Min-max normalize a pandas Series to [0, 1].

    Returns zeros if all values are the same (avoids division by zero).
    """
    smin, smax = s.min(), s.max()
    if smax == smin:
        return pd.Series(0.0, index=s.index)
    return (s - smin) / (smax - smin)


def compute_scores(category):
    """Compute composite scores for all products in a category.

    Returns:
        pd.DataFrame with columns: productid, category, product_name,
        review_count, price_volatility, composite_score, ranked by score.
        Returns None if no data available.
    """
    # --- Load price history ---
    if not os.path.exists(PRICE_HISTORY_FILE):
        logging.warning(f"No price history file found at {PRICE_HISTORY_FILE}")
        return None

    price_df = pd.read_csv(PRICE_HISTORY_FILE)
    price_df = price_df[price_df["category"] == category].copy()

    if price_df.empty:
        logging.warning(f"[{category}] No price history data for this category.")
        return None

    price_df["price"] = pd.to_numeric(price_df["price"], errors="coerce")

    # --- Load reviews for review count ---
    review_file = os.path.join(REVIEWS_DIR, f"{category}_reviews.csv")
    # Fallback for backward compatibility
    if not os.path.exists(review_file):
        review_file = os.path.join(REVIEWS_DIR, "review.csv")

    review_counts = {}
    if os.path.exists(review_file):
        review_df = pd.read_csv(review_file)
        if "category" in review_df.columns:
            review_df = review_df[review_df["category"] == category]
        review_counts = review_df.groupby("productid").size().to_dict()
    else:
        logging.info(f"[{category}] No review file found — using review_count=0 for all products.")

    # --- Compute per-product metrics ---
    grouped = price_df.groupby("productid")
    product_metrics = []

    for pid, group in grouped:
        product_name = group["product_name"].iloc[0]
        n_points = len(group)
        mean_price = group["price"].mean()
        std_price = group["price"].std()

        # Price volatility: coefficient of variation
        # Only meaningful with enough data points
        if n_points >= MIN_HISTORY_POINTS and mean_price > 0 and not pd.isna(std_price):
            volatility = std_price / mean_price
        else:
            volatility = None  # Insufficient history

        review_count = review_counts.get(pid, 0)

        product_metrics.append({
            "productid": pid,
            "category": category,
            "product_name": product_name,
            "review_count": review_count,
            "n_price_points": n_points,
            "price_volatility": volatility,
        })

    metrics_df = pd.DataFrame(product_metrics)

    if metrics_df.empty:
        logging.warning(f"[{category}] No product metrics computed.")
        return None

    # --- Compute composite score ---
    # Normalize review_count
    metrics_df["norm_reviews"] = normalize_series(
        metrics_df["review_count"].fillna(0)
    )

    # For products with sufficient history, normalize volatility
    has_volatility = metrics_df["price_volatility"].notna()

    if has_volatility.any():
        # Normalize volatility only for products that have it
        metrics_df.loc[has_volatility, "norm_volatility"] = normalize_series(
            metrics_df.loc[has_volatility, "price_volatility"]
        )
        # Products without volatility get score based on reviews only
        metrics_df["norm_volatility"] = metrics_df["norm_volatility"].fillna(0)

        metrics_df["composite_score"] = (
            WEIGHT_REVIEWS * metrics_df["norm_reviews"]
            + WEIGHT_VOLATILITY * metrics_df["norm_volatility"]
        )
    else:
        # No products have enough history — rank by review count only
        logging.info(
            f"[{category}] No products have sufficient price history "
            f"(min {MIN_HISTORY_POINTS} points) for volatility scoring. "
            f"Ranking by review_count only."
        )
        metrics_df["norm_volatility"] = 0.0
        metrics_df["composite_score"] = metrics_df["norm_reviews"]

    # Sort by composite score descending
    metrics_df = metrics_df.sort_values("composite_score", ascending=False)

    return metrics_df


def select_top_k(category, top_k=TOP_K):
    """Select top-K products for a category.

    Returns:
        pd.DataFrame of top-K products, or None if no data.
    """
    metrics_df = compute_scores(category)
    if metrics_df is None:
        return None

    top = metrics_df.head(top_k).copy()
    logging.info(
        f"[{category}] Selected top {len(top)} products "
        f"(out of {len(metrics_df)} total)"
    )

    return top


def main(category=None, all_categories=False):
    """Run product selection for one or all categories.

    Saves selection results to data/{category}_top_products.csv.
    """
    if all_categories:
        categories = list(CATEGORIES.keys())
    elif category:
        categories = [category]
    else:
        categories = ["mobiles"]

    os.makedirs(SELECTION_OUTPUT_DIR, exist_ok=True)

    for cat in categories:
        logging.info(f"Computing product scores for: {cat}")
        top_products = select_top_k(cat)

        if top_products is not None and not top_products.empty:
            output_path = os.path.join(
                SELECTION_OUTPUT_DIR, f"{cat}_top_products.csv"
            )
            top_products.to_csv(output_path, index=False, encoding="utf-8-sig")
            logging.info(f"✅ Saved top products: {output_path}")

            # Print summary
            logging.info(f"\n{'='*60}")
            logging.info(f"Top {len(top_products)} products for '{cat}':")
            for _, row in top_products.iterrows():
                vol = row.get("price_volatility")
                vol_str = "N/A" if pd.isna(vol) else f"{float(vol):.4f}"
                logging.info(
                    f"  {row['product_name'][:50]:50s} "
                    f"reviews={row['review_count']:3d} "
                    f"volatility={vol_str} "
                    f"score={row['composite_score']:.4f}"
                )
        else:
            logging.warning(f"[{cat}] No products to select — insufficient data.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Product selection and scoring"
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        choices=list(CATEGORIES.keys()),
        help="Category to score and select"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        dest="all_categories",
        help="Score all configured categories"
    )
    args = parser.parse_args()

    main(category=args.category, all_categories=args.all_categories)
