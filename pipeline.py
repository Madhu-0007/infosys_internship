"""
pipeline.py — End-to-end orchestrator for the E-Commerce Competitor Intelligence Pipeline.

Runs the full flow per category:
  scrape → ingest/clean → append to price_history → score/select top-K
  → forecast → sentiment (only for top-K) → notify

Usage:
    python pipeline.py --category mobiles
    python pipeline.py --category laptops
    python pipeline.py --all

Also callable from the dashboard's Refresh button:
    import pipeline
    pipeline.main(category="mobiles")
"""

import os
import shutil
import logging
import argparse

from config.categories import CATEGORIES

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def rotate_snapshots():
    """Copy today's CSVs to yesterday snapshots for diff-based notifications."""
    try:
        os.makedirs("data", exist_ok=True)
        src_dst_pairs = [
            ("data/mobile.csv", "data/mobile_yesterday.csv"),
            ("data/review.csv", "data/review_yesterday.csv"),
        ]
        for src, dst in src_dst_pairs:
            if os.path.exists(src):
                shutil.copyfile(src, dst)
    except Exception as e:
        logging.warning(f"Snapshot rotation issue: {e}")


def run_pipeline_for_category(category, pages=None):
    """Run the complete end-to-end flow for a single category:
      1. Scrape product & review data (Flipkart & Amazon)
      2. Clean and ingest data
      3. Score and select top-K products
      4. Run time-series forecasting
      5. Run sentiment analysis (for top-K products only)
      6. Run notification checks
    """
    logging.info(f"{'='*60}")
    logging.info(f"Pipeline starting for category: {category}")
    logging.info(f"{'='*60}")

    # Step 1: Scrape
    logging.info("Step 1: Scraping product and review data...")
    rotate_snapshots()
    try:
        import product
        product.main(category=category, pages=pages)
        logging.info("✅ Scraping complete.")
    except Exception as e:
        logging.error(f"Scraping failed for '{category}': {e}")
        # Continue anyway — downstream steps can use existing data

    # Step 2: Ingest / Clean
    logging.info("Step 2: Data ingestion and cleaning...")
    try:
        import ingestion
        ingestion.main(category=category)
        logging.info("✅ Ingestion complete.")
    except Exception as e:
        logging.error(f"Ingestion failed for '{category}': {e}")

    # Step 3: Score / Select top-K
    logging.info("Step 3: Product scoring and selection...")
    try:
        import selection
        selection.main(category=category)
        logging.info("✅ Selection complete.")
    except Exception as e:
        logging.error(f"Selection failed for '{category}': {e}")

    # Step 4: Forecast
    logging.info("Step 4: Time-series price forecasting...")
    try:
        import forecasting
        forecasting.main(category=category)
        logging.info("✅ Forecasting complete.")
    except Exception as e:
        logging.error(f"Forecasting failed for '{category}': {e}")

    # Step 5: Sentiment analysis (only for top-K products)
    logging.info("Step 5: Sentiment analysis (OpenAI)...")
    try:
        import sentiment
        sentiment.main(category=category)
        logging.info("✅ Sentiment analysis complete.")
    except Exception as e:
        logging.error(f"Sentiment analysis failed for '{category}': {e}")

    logging.info(f"Pipeline complete for '{category}'.")

def main(category=None, all_categories=False, pages=None):
    """Run the pipeline for one or all categories.

    Args:
        category: single category name (e.g. 'mobiles')
        all_categories: if True, run for all configured categories
        pages: number of pages to scrape per competitor
    """
    if all_categories:
        categories = list(CATEGORIES.keys())
    elif category:
        if category not in CATEGORIES:
            logging.error(
                f"Unknown category '{category}'. "
                f"Available: {list(CATEGORIES.keys())}"
            )
            return
        categories = [category]
    else:
        categories = ["mobiles"]

    for cat in categories:
        try:
            run_pipeline_for_category(cat, pages=pages)
        except Exception as e:
            logging.error(f"Pipeline failed for '{cat}': {e}")
            continue

    logging.info("All pipeline runs complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="E-Commerce Competitor Intelligence Pipeline"
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        choices=list(CATEGORIES.keys()),
        help="Category to process"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        dest="all_categories",
        help="Process all configured categories"
    )
    parser.add_argument(
        "--pages", "-p",
        type=int,
        default=None,
        help="Number of pages to scrape per competitor (default from categories config: 5)"
    )
    args = parser.parse_args()

    main(category=args.category, all_categories=args.all_categories, pages=args.pages)
