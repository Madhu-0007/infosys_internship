import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime

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

NOTIF_LOG = "data/notifications.csv"   # 📌 dashboard will read this

PRICE_DROP_THRESHOLD = 10  # % drop
NEGATIVE_REVIEW_THRESHOLD = 2  # alerts if new negatives > this

EMAIL_SENDER = os.getenv("EMAIL_ADDRESS")
EMAIL_RECEIVER = "nithinkumarreddy395@gmail.com"  # set your receiver here
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")      # from .env


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
        print(f"⚠ Email send failed: {e}")


# -------------------------------
# LOG TO CSV (for dashboard)
# -------------------------------
def log_notification(notif_type, message):
    os.makedirs(os.path.dirname(NOTIF_LOG), exist_ok=True)

    new_entry = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": notif_type,
        "message": message
    }])

    if os.path.exists(NOTIF_LOG):
        new_entry.to_csv(NOTIF_LOG, mode="a", header=False, index=False)
    else:
        new_entry.to_csv(NOTIF_LOG, index=False)

    print(f"📝 Logged notification: {notif_type}")


# -------------------------------
# PRICE DROP CHECK
# -------------------------------
def check_price_drops():
    if not (os.path.exists(CSV_TODAY_MOBILE) and os.path.exists(CSV_YESTERDAY_MOBILE)):
        print("⚠ Missing mobile CSV files, skipping price check.")
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
                    body = (
                        f"Price Drop Alert 🚨\n\n"
                        f"Product: {row['mobilename_today']}\n"
                        f"Old Price: ₹{old_price}\n"
                        f"New Price: ₹{new_price}\n"
                        f"Drop: {drop_percent:.2f}%\n\n"
                        f"Check competitor site immediately."
                    )
                    subject = f"⚠ Price Drop: {row['mobilename_today']}"
                    send_email(subject, body)
                    log_notification("Price Drop", body)
        except Exception as e:
            print(f"⚠ Error checking price for {row.get('mobilename_today')}: {e}")


# -------------------------------
# NEGATIVE REVIEW CHECK
# -------------------------------
def check_negative_reviews():
    if not (os.path.exists(CSV_TODAY_REVIEW) and os.path.exists(CSV_YESTERDAY_REVIEW)):
        print("⚠ Missing review CSV files, skipping review check.")
        return

    today = pd.read_csv(CSV_TODAY_REVIEW)
    yesterday = pd.read_csv(CSV_YESTERDAY_REVIEW)

    merged = pd.concat([yesterday, today]).drop_duplicates(subset=["productid", "userid", "review"], keep=False)
    negatives = merged[merged["rating"].astype(str).isin(["1", "2"])]

    if len(negatives) >= NEGATIVE_REVIEW_THRESHOLD:
        body = (
            f"Negative Review Alert 🚨\n\n"
            f"Found {len(negatives)} new negative reviews today.\n\n"
            f"Example:\n"
            f"Product: {negatives.iloc[0]['mobilename']}\n"
            f"Review: {negatives.iloc[0]['review']}\n"
            f"Rating: {negatives.iloc[0]['rating']}\n\n"
            f"Check full review report for details."
        )
        send_email("⚠ Negative Reviews Detected", body)
        log_notification("Negative Review", body)


# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    print("🔍 Running notification checks...")
    check_price_drops()
    check_negative_reviews()
    print("✅ Notification run complete.")
