"""
product.py — Multi-category Flipkart scraper with anti-bot hardening.

Supports scraping product listings and reviews for any category defined
in config/categories.py. Uses undetected-chromedriver to reduce bot
detection, randomized delays, rotating User-Agents, and retry logic.

Usage:
    python product.py --category mobiles
    python product.py --category laptops
    python product.py --all

Data is saved to data/ (per-category CSVs) and appended to
data/price_history.csv for time-series tracking.

NOTE: This is a best-effort free anti-bot approach. If Flipkart blocking
persists, proxy rotation may be needed (not implemented — see README).
"""

import os
import re
import time
import random
import logging
import argparse
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup

# Try undetected-chromedriver first, fall back to regular Selenium
try:
    import undetected_chromedriver as uc
    USE_UNDETECTED = True
except ImportError:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from webdriver_manager.chrome import ChromeDriverManager
    USE_UNDETECTED = False
    logging.warning(
        "undetected-chromedriver not installed — falling back to plain Selenium. "
        "Install it with: pip install undetected-chromedriver"
    )

from config.categories import CATEGORIES, DEFAULT_LISTING_PAGES, DEFAULT_REVIEW_PAGES, DEFAULT_OUTPUT_DIR

# ------------------------------
# CONFIG
# ------------------------------
LISTING_PAGES = int(os.getenv("LISTING_PAGES", DEFAULT_LISTING_PAGES))
REVIEW_PAGES = int(os.getenv("REVIEW_PAGES", DEFAULT_REVIEW_PAGES))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", DEFAULT_OUTPUT_DIR)
PRICE_HISTORY_FILE = os.path.join("data", "price_history.csv")

# Min/max random delay between page loads (seconds)
MIN_DELAY = 2
MAX_DELAY = 6

# Max retries per page load before giving up
MAX_RETRIES = 3

# Rotating User-Agent strings to reduce fingerprinting
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

# Ensure output folders exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)

# ------------------------------
# Logging setup
# ------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ------------------------------
# Helpers
# ------------------------------
def random_delay():
    """Sleep for a random duration to mimic human browsing."""
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    time.sleep(delay)


def clean_price(txt):
    """Extract digits from price string."""
    return re.sub(r"[^\d]", "", txt) if txt else None


def make_soup(html):
    """Parse HTML with lxml if available, falling back to standard html.parser."""
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def create_driver():
    """Create a browser driver with anti-bot settings."""
    user_agent = random.choice(USER_AGENTS)

    if USE_UNDETECTED:
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--user-agent={user_agent}")
        driver = uc.Chrome(options=options)
    else:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--user-agent={user_agent}")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # Selenium 4.6+ automatically matches the installed Chrome browser version (e.g. Chrome 152)
        try:
            driver = webdriver.Chrome(options=options)
        except Exception as err:
            logging.info(f"Built-in Selenium driver resolution failed ({err}), trying ChromeDriverManager...")
            driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=options
            )

    return driver


def load_page_with_retry(driver, url, max_retries=MAX_RETRIES):
    """Load a page with exponential backoff retries."""
    for attempt in range(1, max_retries + 1):
        try:
            driver.get(url)
            random_delay()
            return True
        except WebDriverException as e:
            wait_time = 2 ** attempt + random.uniform(0, 1)
            logging.warning(
                f"Page load failed (attempt {attempt}/{max_retries}): {e}. "
                f"Retrying in {wait_time:.1f}s..."
            )
            time.sleep(wait_time)
    logging.error(f"Failed to load {url} after {max_retries} attempts.")
    return False


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


def append_price_history(df_new):
    """Append new rows to the price_history.csv (never overwrites)."""
    if df_new.empty:
        return
    header = not os.path.exists(PRICE_HISTORY_FILE)
    df_new.to_csv(PRICE_HISTORY_FILE, mode="a", header=header, index=False, encoding="utf-8-sig")
    logging.info(f"Appended {len(df_new)} rows to {PRICE_HISTORY_FILE}")


# ------------------------------
# Core scraping functions
# ------------------------------
def scrape_listings(driver, category, pages=LISTING_PAGES):
    """Scrape product listings for a given category.

    Returns:
        tuple: (product_rows list, product_links set)
    """
    config = CATEGORIES[category]
    url_template = config["search_url_template"]
    sel = config["listing_selectors"]
    scraped_at = datetime.utcnow().isoformat()

    product_rows = []
    product_links = set()

    for page in range(1, pages + 1):
        logging.info(f"[{category}] Scraping Flipkart listing page {page}")
        url = url_template.format(page)

        if not load_page_with_retry(driver, url):
            logging.warning(f"[{category}] Skipping page {page} after retries failed.")
            continue

        soup = make_soup(driver.page_source)
        # Try configured selector first
        products = soup.find_all(sel["product_container"]["tag"],
                                 sel["product_container"]["attrs"])
        # Fallback 1: any div with data-id (Flipkart standard product card)
        if not products:
            products = soup.find_all("div", attrs={"data-id": True})
        # Fallback 2: common legacy/alternate container classes
        if not products:
            products = soup.find_all("div", class_=re.compile(r"(tUxRFH|_75nlfW|cPHDOP|_1sdMkc|_4WELSP)"))

        for p in products:
            title_el = (p.find(sel["title"]["tag"], sel["title"]["attrs"]) or
                        p.find(class_=re.compile(r"(RG5Slk|KzDlHZ|wjcEIp|_4rR01T|s1Q9rs)")) or
                        p.find("a", attrs={"title": True}))
            price_el = (p.find(sel["price"]["tag"], sel["price"]["attrs"]) or
                        p.find(class_=re.compile(r"(hZ3P6w|Nx9bqj|_30jeq3|DeU9vF)")))
            mrp_el = (p.find(sel["mrp"]["tag"], sel["mrp"]["attrs"]) or
                      p.find(class_=re.compile(r"(kRYCnD|yRaY8j|_3I9_wc|gxR4EY)")))
            discount_el = (p.find(sel["discount"]["tag"], sel["discount"]["attrs"]) or
                           p.find(class_=re.compile(r"(HQe8jr|UkUFwK|_3Ay6Sb)")))
            rating_el = (p.find(sel["rating"]["tag"], sel["rating"]["attrs"]) or
                         p.find(class_=re.compile(r"(XQDdHH|_3LWZlK|Wphh3L)")))
            link_el = (p.find(sel["link"]["tag"], sel["link"]["attrs"]) or
                       p.find("a", href=re.compile(r"/p/")) or
                       p.find("a", class_=re.compile(r"(k7wcnx|CGtC98|VJA3rP)")))

            product_name = title_el.get_text(strip=True) if title_el else "Unknown"
            price = clean_price(price_el.get_text()) if price_el else None
            mrp_val = (mrp_el.get_text(strip=True).replace("₹", "").replace(",", "")
                       if mrp_el else None)
            discount = discount_el.get_text(strip=True) if discount_el else None
            rating_val = rating_el.get_text(strip=True) if rating_el else None
            url_val = ("https://www.flipkart.com" + link_el["href"]
                       if link_el and link_el.get("href", "").startswith("/")
                       else (link_el["href"] if link_el else None))

            pid = p.get("data-id")
            if not pid and url_val:
                m = re.search(r"pid=([A-Za-z0-9]+)", url_val) or re.search(r"/p/itm([0-9a-z]+)", url_val)
                pid = m.group(1) if m else None

            if url_val:
                product_links.add((pid, product_name, url_val))

            product_rows.append({
                "source": "flipkart",
                "productid": pid,
                "category": category,
                "mobilename": product_name,
                "sellingprice": price,
                "mrp": mrp_val,
                "discountoffering": discount,
                "rating": rating_val,
                "url": url_val,
                "scraped_at": scraped_at,
            })

    # Sentinel check: if no products found, selectors likely broke
    if len(product_rows) == 0:
        logging.error(
            f"[{category}] 0 products found across {pages} pages! "
            f"Selectors likely stale. Check config/categories.py for category "
            f"'{category}' — specifically the 'product_container' selector: "
            f"{sel['product_container']}"
        )

    return product_rows, product_links


def scrape_amazon_listings(driver, category, pages=LISTING_PAGES):
    """Scrape product listings from Amazon.in for a given category.

    Returns:
        list: amazon_rows list of product dicts
    """
    config = CATEGORIES.get(category, {})
    url_template = config.get(
        "amazon_search_url_template",
        f"https://www.amazon.in/s?k={category}&page={{}}"
    )
    scraped_at = datetime.utcnow().isoformat()
    amazon_rows = []

    for page in range(1, pages + 1):
        logging.info(f"[{category}] Scraping Amazon listing page {page}")
        url = url_template.format(page)

        if not load_page_with_retry(driver, url):
            logging.warning(f"[{category}] Skipping Amazon page {page} after retries failed.")
            continue

        soup = make_soup(driver.page_source)
        cards = soup.find_all("div", attrs={"data-component-type": "s-search-result"})
        if not cards:
            cards = soup.find_all("div", attrs={"data-asin": True})

        for c in cards:
            asin = c.get("data-asin")
            if not asin or asin.strip() == "":
                continue

            h2 = c.find("h2")
            title_el = (h2.find("span") if h2 else None) or c.find("span", class_=re.compile(r"a-text-normal"))
            product_name = title_el.get_text(strip=True) if title_el else None
            if not product_name:
                continue

            price_el = c.find("span", class_="a-price-whole") or c.find("span", class_="a-price")
            price = clean_price(price_el.get_text()) if price_el else None

            mrp_el = c.find("span", class_=re.compile(r"a-text-price"))
            mrp_val = clean_price(mrp_el.get_text()) if mrp_el else None

            discount = None
            if price and mrp_val:
                try:
                    p_val, m_val = float(price), float(mrp_val)
                    if m_val > p_val > 0:
                        discount = f"{int(round((m_val - p_val) / m_val * 100))}% off"
                except Exception:
                    pass

            rating_el = c.find("span", class_="a-icon-alt")
            rating_val = None
            if rating_el:
                m = re.search(r"([\d\.]+)\s*out of", rating_el.get_text(strip=True))
                if m:
                    rating_val = m.group(1)

            link_el = (h2.find("a") if h2 else None) or c.find("a", class_=re.compile(r"a-link-normal"))
            url_val = None
            if link_el and link_el.get("href"):
                href = link_el["href"]
                url_val = "https://www.amazon.in" + href if href.startswith("/") else href

            amazon_rows.append({
                "source": "amazon",
                "productid": asin,
                "category": category,
                "mobilename": product_name,
                "sellingprice": price,
                "mrp": mrp_val,
                "discountoffering": discount,
                "rating": rating_val,
                "url": url_val,
                "scraped_at": scraped_at,
            })

    logging.info(f"[{category}] Scraped {len(amazon_rows)} products from Amazon.")
    return amazon_rows


def scrape_reviews(driver, category, product_links):
    """Scrape reviews for a set of product links.

    Args:
        driver: Selenium/UC driver
        category: category name
        product_links: set of (pid, name, url) tuples

    Returns:
        list: review row dicts
    """
    config = CATEGORIES[category]
    rsel = config["review_selectors"]
    review_rows = []

    # Check top 15 products to balance coverage and speed
    links_to_check = list(product_links)[:15]
    logging.info(f"[{category}] Checking reviews for up to {len(links_to_check)} products...")

    for pid, name, url in links_to_check:
        if not url:
            continue
        try:
            if not load_page_with_retry(driver, url):
                continue

            try:
                WebDriverWait(driver, 4).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, rsel["page_loaded"])
                    )
                )
            except TimeoutException:
                pass

            soup = make_soup(driver.page_source)
            all_reviews_link = soup.find("a", href=re.compile(r"/product-reviews/"))

            pages_to_scrape = []
            if all_reviews_link:
                reviews_base = "https://www.flipkart.com" + all_reviews_link["href"]
                for rpage in range(1, REVIEW_PAGES + 1):
                    pages_to_scrape.append(f"{reviews_base}&page={rpage}")

            if pages_to_scrape:
                logging.info(f"[{category}] Scraping reviews page for {name[:40]}")
                for rurl in pages_to_scrape:
                    if not load_page_with_retry(driver, rurl):
                        break
                    rsoup = make_soup(driver.page_source)
                    _extract_reviews_from_soup(rsoup, rsel, pid, name, category, review_rows)
                    random_delay()
            else:
                # Extract any reviews present directly on the product detail page
                _extract_reviews_from_soup(soup, rsel, pid, name, category, review_rows)

        except Exception as e:
            logging.warning(f"[{category}] Error scraping reviews for {name}: {e}")

    return review_rows


def _extract_reviews_from_soup(soup, rsel, pid, name, category, review_rows):
    """Helper to parse review cards from a BeautifulSoup document."""
    containers = soup.find_all(
        rsel["review_container"]["tag"],
        rsel["review_container"]["attrs"]
    )
    if not containers:
        containers = soup.find_all("div", class_=re.compile(r"(cPHDOP|_27M-PJ|EKF0-m)"))

    for c in containers:
        user = (c.find(rsel["user"]["tag"], rsel["user"]["attrs"]) or
                c.find("p", class_=re.compile(r"(_2NsDsF|AwS1CA|_2sc7ZR)")))
        rating = (c.find(rsel["rating"]["tag"], rsel["rating"]["attrs"]) or
                  c.find("div", class_=re.compile(r"(_3LWZlK|XQDdHH)")))
        text = (c.find(rsel["text"]["tag"], rsel["text"]["attrs"]) or
                c.find("div", class_=re.compile(r"(ZmyHeo|_6K-7Co)")))
        if not text and not rating:
            continue

        all_p = c.find_all(
            rsel["date_paragraphs"]["tag"],
            rsel["date_paragraphs"]["attrs"]
        )
        date = all_p[-1].get_text(strip=True) if len(all_p) > 1 else ""

        review_rows.append({
            "source": "flipkart",
            "productid": pid,
            "category": category,
            "mobilename": name,
            "userid": (user.get_text(strip=True) if user else "Anonymous"),
            "review": (text.get_text(strip=True).replace("READ MORE", "") if text else ""),
            "rating": (rating.get_text(strip=True) if rating else None),
            "reviewdate": date,
        })


# ------------------------------
# Main entry point
# ------------------------------
def main(category=None, all_categories=False, pages=None):
    """Run the scraper for one or all categories across Flipkart and Amazon.

    Args:
        category: single category name (e.g. 'mobiles')
        all_categories: if True, scrape all defined categories
        pages: number of listing pages to scrape per competitor
    """
    pages_to_scrape_count = pages or LISTING_PAGES

    if all_categories:
        categories_to_scrape = list(CATEGORIES.keys())
    elif category:
        if category not in CATEGORIES:
            logging.error(
                f"Unknown category '{category}'. "
                f"Available: {list(CATEGORIES.keys())}"
            )
            return
        categories_to_scrape = [category]
    else:
        # Default to mobiles for backward compatibility
        categories_to_scrape = ["mobiles"]

    driver = create_driver()

    try:
        for cat in categories_to_scrape:
            logging.info(f"{'='*50}")
            logging.info(f"Starting dual-competitor scrape for category: {cat} ({pages_to_scrape_count} pages)")
            logging.info(f"{'='*50}")

            try:
                # Step 1: Scrape Flipkart listings
                fk_rows, product_links = scrape_listings(driver, cat, pages=pages_to_scrape_count)
                fk_df = pd.DataFrame(fk_rows)
                if not fk_df.empty:
                    save_csv(
                        fk_df,
                        os.path.join(OUTPUT_DIR, f"{cat}_flipkart_products.csv"),
                        ["productid", "scraped_at"]
                    )

                # Step 2: Scrape Amazon listings
                az_rows = scrape_amazon_listings(driver, cat, pages=pages_to_scrape_count)
                az_df = pd.DataFrame(az_rows)
                if not az_df.empty:
                    save_csv(
                        az_df,
                        os.path.join(OUTPUT_DIR, f"{cat}_amazon_products.csv"),
                        ["productid", "scraped_at"]
                    )

                # Step 3: Match products across competitors (keep ONLY matching products)
                import matcher
                matched_df = pd.DataFrame()
                if not fk_df.empty and not az_df.empty:
                    logging.info(f"[{cat}] Matching {len(fk_df)} Flipkart items with {len(az_df)} Amazon items...")
                    matched_df = matcher.match_competitors(fk_df, az_df)

                if not matched_df.empty:
                    logging.info(
                        f"[{cat}] Retained ONLY {len(matched_df)} matched competitor rows "
                        f"({len(matched_df) // 2} unique products present on BOTH Flipkart & Amazon)."
                    )
                    product_df = matched_df
                else:
                    logging.warning(
                        f"[{cat}] No cross-platform matches found or one competitor was empty. "
                        f"Defaulting to available listings."
                    )
                    product_df = fk_df if not fk_df.empty else az_df

                if not product_df.empty:
                    # Save matched/combined product listing CSV
                    save_csv(
                        product_df,
                        os.path.join(OUTPUT_DIR, f"{cat}_products.csv"),
                        ["productid", "scraped_at"]
                    )
                    # Backward compatibility for notification.py
                    if cat == "mobiles":
                        save_csv(
                            product_df,
                            os.path.join(OUTPUT_DIR, "mobile.csv"),
                            ["productid", "scraped_at"]
                        )

                    # Append to price_history.csv (time-series tracking)
                    history_cols = [
                        c for c in ["productid", "category", "mobilename", "source",
                                    "sellingprice", "mrp", "discountoffering",
                                    "rating", "scraped_at"] if c in product_df.columns
                    ]
                    history_df = product_df[history_cols].rename(columns={
                        "mobilename": "product_name",
                        "sellingprice": "price",
                        "discountoffering": "discount",
                    })
                    append_price_history(history_df)

                # Step 4: Scrape reviews (focused on matched Flipkart products)
                if not matched_df.empty:
                    matched_pids = set(matched_df[matched_df["source"] == "flipkart"]["productid"].dropna())
                    filtered_links = {item for item in product_links if item[0] in matched_pids}
                    if filtered_links:
                        product_links = filtered_links

                review_rows = scrape_reviews(driver, cat, product_links)
                review_df = pd.DataFrame(review_rows)

                if not review_df.empty:
                    save_csv(
                        review_df,
                        os.path.join(OUTPUT_DIR, f"{cat}_reviews.csv"),
                        ["productid", "userid", "review"]
                    )
                    if cat == "mobiles":
                        save_csv(
                            review_df,
                            os.path.join(OUTPUT_DIR, "review.csv"),
                            ["productid", "userid", "review"]
                        )

                logging.info(
                    f"[{cat}] Scrape complete: {len(product_df)} products (matched across competitors), "
                    f"{len(review_rows)} reviews"
                )

            except Exception as e:
                logging.error(f"[{cat}] Category scrape failed — skipping. Error: {e}")
                continue

    finally:
        driver.quit()
        logging.info("Browser closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Dual-competitor scraper (Flipkart & Amazon)"
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        choices=list(CATEGORIES.keys()),
        help="Category to scrape"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        dest="all_categories",
        help="Scrape all configured categories"
    )
    parser.add_argument(
        "--pages", "-p",
        type=int,
        default=LISTING_PAGES,
        help="Number of pages to scrape per competitor (default: 5)"
    )
    args = parser.parse_args()

    main(category=args.category, all_categories=args.all_categories, pages=args.pages)
