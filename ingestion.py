#ingestion.py 

import pandas as pd
from datetime import datetime, timedelta
import re
import os
import logging
from textblob import TextBlob  # for sentiment analysis
import lightgbm as lgb
import joblib

# ---------------- CONFIG ----------------
REVIEWS_FILE = os.getenv("REVIEWS_FILE", "my_docs/review.csv")   # cleaned review input
MOBILE_FILE = os.getenv("MOBILE_FILE", "my_docs/mobile.csv")    # scraped mobile data input
OUTPUT_REVIEWS = os.getenv("OUTPUT_REVIEWS", "cleaned_reviews.csv")
OUTPUT_MOBILE = os.getenv("OUTPUT_MOBILE", "cleaned_mobile.csv")
DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- Logging Setup ----------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ---------------- FUNCTIONS ----------------

def parse_relative_date(text):
    """Convert relative dates like '22 days ago' to absolute date safely"""
    text = str(text).strip().lower()
    now = datetime.now()
    try:
        if "day" in text:
            match = re.search(r"(\d+)", text)
            days = int(match.group(1)) if match else 0
            return (now - timedelta(days=days)).date()
        elif "month" in text:
            match = re.search(r"(\d+)", text)
            months = int(match.group(1)) if match else 0
            month = now.month - months
            year = now.year
            if month <= 0:
                month += 12
                year -= 1
            day = min(now.day, 28)
            return datetime(year, month, day).date()
        elif "year" in text:
            match = re.search(r"(\d+)", text)
            years = int(match.group(1)) if match else 0
            return datetime(now.year - years, now.month, now.day).date()
        else:
            dt = pd.to_datetime(text, errors='coerce')
            if pd.isna(dt):
                return None
            return dt.date()
    except Exception:
        return None

def remove_emojis(text):
    """Remove emojis, symbols, and non-text characters from review"""
    if not isinstance(text, str):
        return text
    return re.sub(r'[^A-Za-z0-9.,!?;:\'"()\-\s]', '', text)

# ---------------- CLEANING FUNCTIONS ----------------

def clean_reviews(df):
    """Clean review DataFrame"""
    df['mobilename'] = df['mobilename'].astype(str).str.strip()
    df['userid'] = df['userid'].astype(str).str.strip()
    df['review'] = df['review'].astype(str).str.strip()
    df['review'] = df['review'].apply(remove_emojis)
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    df['reviewdate'] = df['reviewdate'].apply(parse_relative_date)
    df = df[df['review'].str.len() > 0]
    df = df.drop_duplicates(subset=['productid', 'userid', 'review'])
    return df

def clean_mobile(df):
    """Clean mobile/product DataFrame"""
    df['mobilename'] = df['mobilename'].astype(str).str.strip()
    df['source'] = df['source'].astype(str).str.strip()
    df['sellingprice'] = pd.to_numeric(df['sellingprice'], errors='coerce')
    df['discountoffering'] = df['discountoffering'].astype(str).str.replace('% off','',regex=False).str.strip()
    df['discountoffering'] = pd.to_numeric(df['discountoffering'], errors='coerce')
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    df['scraped_at'] = pd.to_datetime(df['scraped_at'], errors='coerce')
    df = df.drop_duplicates(subset=['productid', 'scraped_at'], keep='last')
    return df

# ---------------- MAIN ----------------

def main():
    # -------- Load and Clean Mobile Data --------
    if os.path.exists(MOBILE_FILE):
        df_mobile = pd.read_csv(MOBILE_FILE)
        logging.info(f"Raw mobile data: {len(df_mobile)} rows")
        df_mobile_clean = clean_mobile(df_mobile)
        valid_product_ids = set(df_mobile_clean['productid'].dropna().unique())
        logging.info(f"Cleaned mobile data: {len(df_mobile_clean)} rows")
        df_mobile_clean.to_csv(os.path.join(DATA_DIR, OUTPUT_MOBILE), index=False, encoding="utf-8-sig")
        logging.info(f"✅ Cleaned mobile data saved: {DATA_DIR}/{OUTPUT_MOBILE}")

        train_price_model_lgbm(df_mobile_clean)
    else:
        logging.warning(f"Mobile file not found: {MOBILE_FILE}")

    # -------- Load and Clean Reviews --------
    if os.path.exists(REVIEWS_FILE):
        df_reviews = pd.read_csv(REVIEWS_FILE)
        logging.info(f"Raw reviews: {len(df_reviews)} rows")

        # ✅ Filter only reviews whose productid exists in mobiles.csv
        if valid_product_ids:
            before = len(df_reviews)
            df_reviews = df_reviews[df_reviews['productid'].isin(valid_product_ids)]
            logging.info(f"Filtered reviews by productid: {len(df_reviews)} rows (kept {len(df_reviews)}/{before})")

        df_reviews_clean = clean_reviews(df_reviews)
        logging.info(f"Cleaned reviews: {len(df_reviews_clean)} rows")
        df_reviews_clean.to_csv(os.path.join(DATA_DIR, OUTPUT_REVIEWS), index=False, encoding="utf-8-sig")
        logging.info(f"✅ Cleaned reviews saved: {DATA_DIR}/{OUTPUT_REVIEWS}")
    else:
        logging.warning(f"Reviews file not found: {REVIEWS_FILE}")

def train_price_model_lgbm(mobile_df):
    features = ["discountoffering", "rating"]
    # Ensure columns exist and are numeric
    for col in features:
        if col not in mobile_df.columns:
            logging.warning(f"Missing column for ML: {col}")
            return
    mobile_df = mobile_df.dropna(subset=["sellingprice", "discountoffering", "rating"])
    if len(mobile_df) < 10:
        logging.warning("Not enough data to train LightGBM model.")
        return
    X = mobile_df[features]
    y = mobile_df["sellingprice"]
    model = lgb.LGBMRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    joblib.dump(model, "data/price_predictor_lgbm.joblib")
    logging.info("✅ LightGBM price prediction model trained and saved.")

if __name__ == "__main__":
    main()