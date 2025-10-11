import pandas as pd
import time
import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

# --- Load API Key Securely from .env file ---
# This path assumes your .env file is inside a folder named 'env'
# If your .env file is in the same folder as the script, use: load_dotenv()
load_dotenv(dotenv_path="env/.env")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not found. Please ensure 'env/.env' exists and contains OPENAI_API_KEY.")
client = OpenAI(api_key=api_key)


# --- Main Configuration ---
INPUT_FILE = "data/cleaned_reviews.csv"
OUTPUT_FILE = "reviews_with_sentiment.csv"
REVIEW_COLUMN = "review" # The column in your CSV with the review text
MODEL = "gpt-4o-mini"
BATCH_SIZE = 20
RETRY_DELAY_SECONDS = 60


def clean_review_text(text: str) -> str:
    """Cleans the review text for processing."""
    if not isinstance(text, str):
        return ""
    text = text.strip().lower()
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text

def parse_sentiments(api_output: str, expected_count: int) -> list[str]:
    """Robustly parses sentiment labels from the API response."""
    sentiments = re.findall(r'(?im)^\s*\d+\s*[:.]?\s*(Positive|Negative|Neutral)', api_output)
    
    if len(sentiments) != expected_count:
        print(f"\n--- PARSING WARNING ---")
        print(f"Expected {expected_count} sentiments, but found {len(sentiments)}.")
        print(f"RAW API OUTPUT:\n{api_output}")
        return ["Parsing Error"] * expected_count
        
    return sentiments

def get_sentiments_for_batch(reviews: list[str]) -> list[str]:
    """Sends a batch of reviews to the OpenAI API and gets sentiment classifications."""
    reviews_text = "\n".join([f"{i+1}. {review}" for i, review in enumerate(reviews)])
    
    system_prompt = """
    You are a highly accurate sentiment analysis expert. Classify the sentiment for each numbered review as 'Positive', 'Negative', or 'Neutral'.
    - Positive: Clear satisfaction or praise.
    - Negative: Clear dissatisfaction or criticism.
    - Neutral: Purely informational or no strong emotion.
    Your response MUST strictly follow the format '1: <Sentiment>', '2: <Sentiment>', etc., with no extra text.
    """
    
    user_prompt = f"Please classify the sentiment for the following reviews:\n\n{reviews_text}"
    
    while True:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0,
                seed=42
            )
            output = response.choices[0].message.content.strip()
            return parse_sentiments(output, len(reviews))
        except Exception as e:
            print(f"\nAn API error occurred: {e}. Retrying in {RETRY_DELAY_SECONDS}s...")
            time.sleep(RETRY_DELAY_SECONDS)

# --- Main Script Logic ---
print("🚀 Starting sentiment analysis process...")

# --- 1. Load Source Data (with better error handling) ---
if not os.path.exists(INPUT_FILE):
    print(f"❌ ERROR: Input file not found at '{INPUT_FILE}'.")
    print("Please make sure the file exists and the path is correct.")
    exit()

try:
    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Successfully loaded {len(df)} rows from {INPUT_FILE}.")
except Exception as e:
    print(f"❌ ERROR: Could not read the CSV file. Reason: {e}")
    exit()

# --- 2. Load Already Processed Data ---
if os.path.exists(OUTPUT_FILE):
    try:
        df_processed = pd.read_csv(OUTPUT_FILE)
        # Ensure required columns exist before creating the ID set
        if 'productid' in df_processed.columns and 'userid' in df_processed.columns:
            processed_ids = set(df_processed['productid'].astype(str) + "_" + df_processed['userid'].astype(str))
            print(f"✅ Found {len(df_processed)} already processed reviews in {OUTPUT_FILE}.")
        else:
            print(f"⚠️ WARNING: Output file '{OUTPUT_FILE}' is missing 'productid' or 'userid'. Treating as empty.")
            df_processed = pd.DataFrame()
            processed_ids = set()
    except Exception as e:
        print(f"⚠️ WARNING: Could not read the existing output file. Starting fresh. Reason: {e}")
        df_processed = pd.DataFrame()
        processed_ids = set()
else:
    df_processed = pd.DataFrame()
    processed_ids = set()

# --- 3. Filter for Unprocessed Reviews ---
# Ensure source dataframe has the required columns
if 'productid' not in df.columns or 'userid' not in df.columns:
    print("❌ ERROR: Input file is missing 'productid' or 'userid' columns, which are required to track progress.")
    exit()
    
df['_unique_id'] = df['productid'].astype(str) + "_" + df['userid'].astype(str)
unprocessed_df = df[~df['_unique_id'].isin(processed_ids)].copy()

if unprocessed_df.empty:
    print("\n🎉 No new reviews to process. All done!")
    exit()

print(f"\n🔍 Found {len(unprocessed_df)} new reviews to process.")

# --- 4. Process New Reviews in Batches with a Progress Bar ---
all_new_sentiments = []
# Using tqdm for a visual progress bar
for i in tqdm(range(0, len(unprocessed_df), BATCH_SIZE), desc="Analyzing Batches"):
    batch_df = unprocessed_df.iloc[i:i + BATCH_SIZE]
    batch_reviews = batch_df[REVIEW_COLUMN].fillna("").astype(str).tolist()
    
    sentiments = get_sentiments_for_batch(batch_reviews)
    all_new_sentiments.extend(sentiments)

# --- 5. Combine and Save Results ---
unprocessed_df['sentiment'] = all_new_sentiments

# Combine with previously processed data
final_df = pd.concat([df_processed, unprocessed_df.drop(columns=['_unique_id'])], ignore_index=True)
final_df.to_csv(OUTPUT_FILE, index=False)

print("\n✅ Sentiment analysis complete!")
print(f"Results saved to {OUTPUT_FILE}")
print("\n--- Sample of Processed Reviews ---")
print(final_df[[REVIEW_COLUMN, "sentiment"]].tail(10))
print("\n--- Final Sentiment Distribution ---")
print(final_df["sentiment"].value_counts())