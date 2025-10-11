print("DEBUG: notification.py module imported!")

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

NOTIF_LOG = "data/notifications.csv"  # 📌 dashboard will read this

PRICE_DROP_THRESHOLD = 10  # % drop
NEGATIVE_REVIEW_THRESHOLD = 2  # alerts if new negatives > this

EMAIL_SENDER = os.getenv("EMAIL_ADDRESS")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")      # from .env

# --- THE FIX: Load the IDs of already sent notifications ---
def get_sent_notification_ids():
    """Reads the unique IDs from the log file to prevent duplicates."""
    if not os.path.exists(NOTIF_LOG):
        return []
    try:
        df = pd.read_csv(NOTIF_LOG)
        if "unique_id" in df.columns:
            return df["unique_id"].tolist()
        return []
    except pd.errors.EmptyDataError:
        return []

# -------------------------------
# EMAIL HELPER
# -------------------------------
def send_email(subject, body):
    print(f"DEBUG: Attempting to send email to {EMAIL_RECEIVER} with subject '{subject}'")
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
def log_notification(notif_type, message, unique_id):
    """Logs a notification and its unique ID to prevent duplicates."""
    os.makedirs(os.path.dirname(NOTIF_LOG), exist_ok=True)

    new_entry = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": notif_type,
        "message": message,
        "unique_id": unique_id  # Add the unique ID to the log
    }])

    if os.path.exists(NOTIF_LOG) and os.path.getsize(NOTIF_LOG) > 0:
        new_entry.to_csv(NOTIF_LOG, mode="a", header=False, index=False)
    else:
        new_entry.to_csv(NOTIF_LOG, index=False)

    print(f"📝 Logged notification: {notif_type}")


# -------------------------------
# PRICE DROP CHECK
# -------------------------------
def check_price_drops(sent_ids):
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
                    # --- THE FIX: Create and check the unique ID ---
                    unique_id = f"price-{row['productid']}-{old_price}-{new_price}"
                    if unique_id in sent_ids:
                        continue  # Skip if we already sent this alert

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
                    log_notification("Price Drop", body, unique_id)
                    sent_ids.append(unique_id) # Update our list of sent IDs for this run

        except Exception as e:
            print(f"⚠ Error checking price for {row.get('mobilename_today')}: {e}")


# -------------------------------
# NEGATIVE REVIEW CHECK
# -------------------------------
def check_negative_reviews(sent_ids):
    if not (os.path.exists(CSV_TODAY_REVIEW) and os.path.exists(CSV_YESTERDAY_REVIEW)):
        print("⚠ Missing review CSV files, skipping review check.")
        return

    today = pd.read_csv(CSV_TODAY_REVIEW).drop_duplicates()
    yesterday = pd.read_csv(CSV_YESTERDAY_REVIEW).drop_duplicates()

    # A better way to find *only* new reviews
    merged = today.merge(yesterday, on=['productid', 'userid', 'review'], how='left', indicator=True)
    new_reviews = merged[merged['_merge'] == 'left_only']
    
    negatives = new_reviews[new_reviews["rating_x"].astype(str).isin(["1", "2"])]

    if len(negatives) >= NEGATIVE_REVIEW_THRESHOLD:
        print(f"Found {len(negatives)} new negative reviews. Sending alerts.")
        # Send one alert per new negative review to track them individually
        for _, row in negatives.iterrows():
            # --- THE FIX: Create and check the unique ID for the review ---
            unique_id = f"review-{row['productid']}-{row['userid']}-{row['review']}"
            if unique_id in sent_ids:
                continue # Skip if already sent
            
            body = (
                f"Negative Review Alert 🚨\n\n"
                f"A new negative review was found.\n\n"
                f"Product: {row['mobilename_x']}\n"
                f"Review: {row['review']}\n"
                f"Rating: {row['rating_x']}\n"
            )
            subject = f"⚠ New Negative Review for {row['mobilename_x']}"
            send_email(subject, body)
            log_notification("Negative Review", body, unique_id)
            sent_ids.append(unique_id)


# -------------------------------
# TEST NOTIFICATION
# -------------------------------
def send_test_notification(streamlit_callback=None):
    try:
        print("Sending test notification email...")
        send_email("Test Notification", "This is a test notification email from your dashboard integration.")
        print("Test notification email sent.")
        if streamlit_callback:
            streamlit_callback("✅ Test notification email sent.")
    except Exception as e:
        print(f"⚠ Test notification email failed: {e}")
        if streamlit_callback:
            streamlit_callback(f"⚠ Test notification email failed: {e}")


# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    print("🔍 Running notification checks...")
    # Get the list of IDs we've already sent alerts for
    sent_notification_ids = get_sent_notification_ids()
    check_price_drops(sent_notification_ids)
    check_negative_reviews(sent_notification_ids)
    print("✅ Notification run complete.")
    send_test_notification()