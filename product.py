"""
Simplified production-ready Flipkart scraper
(Intern-friendly, saves to my_docs/ folder)
"""

import os, re, time, logging
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# ------------------------------
# CONFIG
# ------------------------------
SEARCH_URL = "https://www.flipkart.com/search?q=mobiles&page={}"
LISTING_PAGES = int(os.getenv("LISTING_PAGES", 3))
REVIEW_PAGES = int(os.getenv("REVIEW_PAGES", 2))
WAIT = int(os.getenv("WAIT", 3))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "my_docs")

# ensure output folder
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------
# Logging setup
# ------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ------------------------------
# Selenium setup
# ------------------------------
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_experimental_option('excludeSwitches', ['enable-logging'])

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

# ------------------------------
# Helpers
# ------------------------------
def clean_price(txt):
    """Extract digits from price string."""
    return re.sub(r"[^\d]", "", txt) if txt else None

def save_csv(df_new, path, subset_cols):
    """Append to CSV if exists, drop duplicates."""
    if os.path.exists(path):
        df_old = pd.read_csv(path)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new
    if subset_cols:
        df = df.drop_duplicates(subset=subset_cols, keep="last")
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logging.info(f"Saved {len(df_new)} new rows (total {len(df)}) → {path}")

# ------------------------------
# Step 1: Collect product listings
# ------------------------------
mobile_rows, product_links = [], set()
scraped_at = datetime.utcnow().isoformat()

for page in range(1, LISTING_PAGES + 1):
    logging.info(f"Scraping listing page {page}")
    driver.get(SEARCH_URL.format(page))
    time.sleep(WAIT)
    soup = BeautifulSoup(driver.page_source, "lxml")

    products = soup.find_all("div", {"class": "tUxRFH"})
    for p in products:
        title = p.find("div", {"class": "KzDlHZ"})
        price = p.find("div", {"class": "Nx9bqj _4b5DiR"})
        mrp = p.find("div", {"class": "yRaY8j"})
        discount = p.find("div", {"class": "UkUFwK"})
        rating = p.find("div", {"class": "XQDdHH"})
        link = p.find("a", {"class": "CGtC98"})

        mobilename = title.get_text(strip=True) if title else "Unknown"
        sellingprice = clean_price(price.get_text()) if price else None
        mrp_val = mrp.get_text(strip=True).replace("₹","").replace(",","") if mrp else None
        discountoffering = discount.get_text(strip=True) if discount else None
        rating_val = rating.get_text(strip=True) if rating else None
        url = "https://www.flipkart.com" + link["href"] if link else None

        pid = None
        if url:
            m = re.search(r"/p/itm([0-9a-z]+)", url)
            pid = m.group(1) if m else None
            product_links.add((pid, mobilename, url))

        mobile_rows.append({
            "source": "flipkart",
            "productid": pid,
            "mobilename": mobilename,
            "sellingprice": sellingprice,
            "mrp": mrp_val,
            "discountoffering": discountoffering,
            "rating": rating_val,
            "url": url,
            "scraped_at": scraped_at
        })

# save product listings
mobile_df = pd.DataFrame(mobile_rows)
save_csv(mobile_df, os.path.join(OUTPUT_DIR, "mobile.csv"), ["productid","scraped_at"])

# ------------------------------
# Step 2: Collect product reviews
# ------------------------------
review_rows = []

for pid, name, url in product_links:
    if not url: 
        continue
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "VU-ZEz")))
        soup = BeautifulSoup(driver.page_source, "lxml")
        all_reviews = soup.find("a", href=re.compile("/product-reviews/"))
        if not all_reviews: 
            continue

        reviews_base = "https://www.flipkart.com" + all_reviews["href"]
        logging.info(f"Scraping reviews for {name}")

        for rpage in range(1, REVIEW_PAGES + 1):
            driver.get(f"{reviews_base}&page={rpage}")
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "cPHDOP")))
            except TimeoutException:
                break

            rsoup = BeautifulSoup(driver.page_source, "lxml")
            containers = rsoup.find_all("div", {"class": "cPHDOP"})

            for c in containers:
                user = c.find("p", {"class": "_2NsDsF AwS1CA"})
                rating = c.find("div", {"class": "_3LWZlK"})
                text = c.find("div", {"class": "ZmyHeo"})
                all_p = c.find_all("p", {"class": "_2NsDsF"})
                date = all_p[-1].get_text(strip=True) if len(all_p) > 1 else ""

                review_rows.append({
                    "source": "flipkart",
                    "productid": pid,
                    "mobilename": name,
                    "userid": user.get_text(strip=True) if user else "Anonymous",
                    "review": text.get_text(strip=True).replace("READ MORE","") if text else "",
                    "rating": rating.get_text(strip=True) if rating else None,
                    "reviewdate": date
                })
            time.sleep(1)
    except Exception as e:
        logging.warning(f"Error scraping {name}: {e}")

driver.quit()

# save reviews
review_df = pd.DataFrame(review_rows)
save_csv(review_df, os.path.join(OUTPUT_DIR, "review.csv"), ["productid","userid","review"])

# ------------------------------
# Optional ingestion call
# ------------------------------
try:
    import ingestion
    ingestion.main()
except ImportError:
    logging.info("ingestion.py not found, skipping ingestion step.")
