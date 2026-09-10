"""
matcher.py — Cross-competitor product matching engine (Flipkart vs Amazon).

Matches products between Flipkart and Amazon using:
  1. Brand extraction & strict compatibility check
  2. Hardware specification extraction (RAM, SSD, Processor/CPU, Screen size)
  3. Token overlap similarity on model/series names
  4. Keeps ONLY products that are found on BOTH competitor platforms.

Usage:
    python matcher.py --category laptops
"""

import os
import re
import logging
import argparse
import pandas as pd
import numpy as np

# Supported major brands for cross-platform identification
KNOWN_BRANDS = [
    "apple", "samsung", "lenovo", "asus", "hp", "dell", "acer", "msi",
    "motorola", "realme", "xiaomi", "redmi", "oneplus", "vivo", "oppo", "poco",
    "whirlpool", "lg", "ifb", "haier", "bosch", "godrej", "philips",
    "primebook", "infinix", "honor", "iqoo"
]

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def clean_text(text: str) -> str:
    """Normalize text by lowercasing and stripping punctuation/noise."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    # Normalize common abbreviations
    text = re.sub(r"\b(intel|amd|nvidia|graphics|laptop|notebook|thin and light|smartchoice)\b", " ", text)
    text = re.sub(r"[^\w\s\.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_brand(title: str) -> str:
    """Detect brand name from title."""
    title_lower = str(title).lower()
    for brand in KNOWN_BRANDS:
        if re.search(rf"\b{brand}\b", title_lower):
            return brand
    # Fallback to first word if no known brand matches
    words = title_lower.split()
    return words[0] if words else "unknown"


def extract_specs(title: str) -> dict:
    """Extract key hardware specifications from title."""
    t = str(title).lower()
    specs = {}

    # RAM (e.g. 8gb, 16 gb, 32gb)
    ram = re.search(r"\b(4|8|12|16|24|32|64)\s*(?:gb|g)\s*(?:ddr\d|lpddr\d|ram)?\b", t)
    if ram:
        specs["ram"] = f"{ram.group(1)}gb"

    # Storage (e.g. 128gb, 256gb, 512gb, 1tb, 2tb)
    storage = re.search(r"\b(128|256|512)\s*(?:gb|g)\b", t)
    tb = re.search(r"\b(1|2)\s*(?:tb|t)\b", t)
    if tb:
        specs["storage"] = f"{tb.group(1)}tb"
    elif storage:
        specs["storage"] = f"{storage.group(1)}gb"

    # Processor series (e.g. i3, i5, i7, i9, ryzen 3, ryzen 5, ryzen 7, celeron, pentium, m1, m2, m3)
    cpu = re.search(r"\b(i3|i5|i7|i9|core\s*3|core\s*5|core\s*7|ryzen\s*[3579]|celeron|pentium|m1|m2|m3|kompanio|snapdragon)\b", t)
    if cpu:
        specs["cpu"] = cpu.group(1).replace(" ", "")

    # Processor model number (e.g. 1215u, 7520u, 7320u, 1334u, 13420h, n4500, n4020)
    cpu_model = re.search(r"\b(1\d{3}[a-z]|7\d{3}[a-z]|n\d{4}|5\d{3}[a-z])\b", t)
    if cpu_model:
        specs["cpu_model"] = cpu_model.group(1)

    return specs


def compute_match_score(title_a: str, title_b: str) -> float:
    """Compute matching confidence between two product titles (0.0 to 1.0)."""
    brand_a = extract_brand(title_a)
    brand_b = extract_brand(title_b)

    # Hard gate: Brands must match if known
    if brand_a != "unknown" and brand_b != "unknown" and brand_a != brand_b:
        return 0.0

    specs_a = extract_specs(title_a)
    specs_b = extract_specs(title_b)

    # If both specify CPU model (e.g. 7320u vs 1215u) and they differ, reject
    if "cpu_model" in specs_a and "cpu_model" in specs_b:
        if specs_a["cpu_model"] != specs_b["cpu_model"]:
            return 0.0

    # If both specify CPU family (e.g. i3 vs i5) and they differ, reject
    if "cpu" in specs_a and "cpu" in specs_b:
        if specs_a["cpu"] != specs_b["cpu"]:
            return 0.0

    # If both specify storage and they differ, penalize heavily
    if "storage" in specs_a and "storage" in specs_b:
        if specs_a["storage"] != specs_b["storage"]:
            return 0.2

    # If both specify RAM and they differ, penalize heavily
    if "ram" in specs_a and "ram" in specs_b:
        if specs_a["ram"] != specs_b["ram"]:
            return 0.2

    # Token overlap calculation
    tokens_a = set(clean_text(title_a).split())
    tokens_b = set(clean_text(title_b).split())

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)
    # Dice coefficient
    score = (2.0 * len(intersection)) / (len(tokens_a) + len(tokens_b))

    # Bonus if key specs matched
    if specs_a.get("cpu_model") and specs_a.get("cpu_model") == specs_b.get("cpu_model"):
        score = min(1.0, score + 0.3)
    if specs_a.get("cpu") and specs_a.get("cpu") == specs_b.get("cpu"):
        score = min(1.0, score + 0.15)
    if specs_a.get("storage") and specs_a.get("storage") == specs_b.get("storage"):
        score = min(1.0, score + 0.1)

    return score


def match_competitors(flipkart_df: pd.DataFrame, amazon_df: pd.DataFrame, min_threshold: float = 0.50) -> pd.DataFrame:
    """Pair Flipkart and Amazon products. Keep ONLY products present in BOTH.

    Returns:
        pd.DataFrame: Combined DataFrame containing matched Flipkart and Amazon rows,
                      unified by a common 'matched_id' and 'product_name'.
    """
    if flipkart_df.empty or amazon_df.empty:
        logging.warning("One or both competitor datasets are empty. Cannot perform cross-matching.")
        return pd.DataFrame()

    matched_pairs = []
    used_amazon_idx = set()

    for fk_idx, fk_row in flipkart_df.iterrows():
        fk_title = fk_row.get("mobilename") or fk_row.get("product_name") or ""
        best_score = 0.0
        best_az_idx = None

        for az_idx, az_row in amazon_df.iterrows():
            if az_idx in used_amazon_idx:
                continue

            az_title = az_row.get("mobilename") or az_row.get("product_name") or ""
            score = compute_match_score(fk_title, az_title)

            if score > best_score:
                best_score = score
                best_az_idx = az_idx

        if best_score >= min_threshold and best_az_idx is not None:
            used_amazon_idx.add(best_az_idx)
            az_row = amazon_df.loc[best_az_idx]

            matched_id = f"MATCH_{len(matched_pairs) + 1:04d}"
            # Choose a clean canonical display name (shortest or most descriptive)
            canonical_name = fk_title if len(fk_title) < len(az_row.get("mobilename", "")) else az_row.get("mobilename", fk_title)

            fk_copy = fk_row.to_dict()
            fk_copy["matched_id"] = matched_id
            fk_copy["canonical_name"] = canonical_name
            fk_copy["mobilename"] = canonical_name
            fk_copy["source"] = "flipkart"

            az_copy = az_row.to_dict()
            az_copy["matched_id"] = matched_id
            az_copy["canonical_name"] = canonical_name
            az_copy["mobilename"] = canonical_name
            az_copy["source"] = "amazon"

            matched_pairs.extend([fk_copy, az_copy])

    if not matched_pairs:
        logging.warning(f"No matching products found between Flipkart ({len(flipkart_df)}) and Amazon ({len(amazon_df)}) at threshold {min_threshold}.")
        return pd.DataFrame()

    matched_df = pd.DataFrame(matched_pairs)
    logging.info(f"✅ Successfully matched {len(matched_df) // 2} identical products across Flipkart & Amazon!")
    return matched_df


def filter_and_save_matched(category: str, output_dir: str = "data", data_dir: str = "data") -> pd.DataFrame:
    """Load scraped Flipkart and Amazon files, match them, and save matched-only dataset."""
    fk_file = os.path.join(output_dir, f"{category}_products.csv")
    az_file = os.path.join(output_dir, f"{category}_amazon_products.csv")

    if not os.path.exists(fk_file) or not os.path.exists(az_file):
        logging.warning(f"Missing competitor files for '{category}' ({fk_file} or {az_file}).")
        return pd.DataFrame()

    fk_df = pd.read_csv(fk_file)
    az_df = pd.read_csv(az_file)

    matched_df = match_competitors(fk_df, az_df)
    if not matched_df.empty:
        out_path = os.path.join(data_dir, f"{category}_matched_products.csv")
        os.makedirs(data_dir, exist_ok=True)
        matched_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        logging.info(f"Saved matched dual-competitor products: {out_path}")

    return matched_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross-competitor product matcher")
    parser.add_argument("--category", "-c", type=str, default="laptops")
    args = parser.parse_args()
    filter_and_save_matched(args.category)
