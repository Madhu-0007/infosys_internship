import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# -------------------------------
# LOAD ENV
# -------------------------------
load_dotenv(dotenv_path="env/.env")

# -------------------------------
# CONFIG
# -------------------------------
CSV_TODAY_MOBILE = "My_docs/mobile.csv"
CSV_YESTERDAY_MOBILE = "My_docs/mobile_yesterday.csv"

CSV_TODAY_REVIEW = "My_docs/review.csv"
CSV_YESTERDAY_REVIEW = "My_docs/review_yesterday.csv"

PRICE_DROP_THRESHOLD = 10  # % drop
NEGATIVE_REVIEW_THRESHOLD = 2  # alerts if new negatives > this

EMAIL_SENDER = os.getenv("EMAIL_ADDRESS")
EMAIL_RECEIVER = "nithinkumarreddy395@gmail.com"   # 📌 set your receiver here
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # from .env

# -------------------------------
# EMAIL HELPER
# -------------------------------
def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        print(f"📧 Email sent → {subject}")
    except Exception as e:
        print(f"⚠️ Email send failed: {e}")

# -------------------------------
# PRICE DROP CHECK
# -------------------------------
def check_price_drops():
    if not (os.path.exists(CSV_TODAY_MOBILE) and os.path.exists(CSV_YESTERDAY_MOBILE)):
        print("⚠️ Missing mobile CSV files, skipping price check.")
        return

    today = pd.read_csv(CSV_TODAY_MOBILE)
    yesterday = pd.read_csv(CSV_YESTERDAY_MOBILE)

    merged = pd.merge(today, yesterday, on="productid", suffixes=("_today", "_yesterday"))

    for _, row in merged.iterrows():
        try:
            old_price = float(row["sellingprice_yesterday"])
            new_price = float(row["sellingprice_today"])

            if old_price > 0:
                drop_percent = ((old_price - new_price) / old_price) * 100
                if drop_percent >= PRICE_DROP_THRESHOLD:
                    body = f"""
                    Price Drop Alert 🚨

                    Product: {row['mobilename_today']}
                    Old Price: ₹{old_price}
                    New Price: ₹{new_price}
                    Drop: {drop_percent:.2f}%

                    Check competitor site immediately.
                    """
                    send_email(f"⚠️ Price Drop: {row['mobilename_today']}", body)
        except Exception as e:
            print(f"⚠️ Error checking price for {row.get('mobilename_today')}: {e}")

# -------------------------------
# NEGATIVE REVIEW CHECK
# -------------------------------
def check_negative_reviews():
    if not (os.path.exists(CSV_TODAY_REVIEW) and os.path.exists(CSV_YESTERDAY_REVIEW)):
        print("⚠️ Missing review CSV files, skipping review check.")
        return

    today = pd.read_csv(CSV_TODAY_REVIEW)
    yesterday = pd.read_csv(CSV_YESTERDAY_REVIEW)

    merged = pd.concat([yesterday, today]).drop_duplicates(subset=["productid", "userid", "review"], keep=False)

    negatives = merged[merged["rating"].astype(str).isin(["1", "2"])]

    if len(negatives) >= NEGATIVE_REVIEW_THRESHOLD:
        body = f"""
        Negative Review Alert 🚨

        Found {len(negatives)} new negative reviews today.

        Example:
        Product: {negatives.iloc[0]['mobilename']}
        Review: {negatives.iloc[0]['review']}
        Rating: {negatives.iloc[0]['rating']}

        Check full review report for details.
        """
        send_email("⚠️ Negative Reviews Detected", body)

# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    print("🔍 Running notification checks...")
    check_price_drops()
    check_negative_reviews()
    print("✅ Notification run complete.")
