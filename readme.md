# 🛒 E-Commerce Competitor Strategy Dashboard

A dual-platform (Flipkart vs Amazon) competitor intelligence terminal for
**Mobiles**, **Laptops**, and **Home Appliances**. Tracks live pricing,
forecasts prices with Holt-Winters exponential smoothing, analyses real
customer sentiment, and surfaces actionable competitor insights — all in an
interactive Streamlit dark-terminal dashboard.

---

## Architecture

```
   ┌─────────────┐        ┌─────────────┐
   │  Flipkart   │        │   Amazon    │
   └──────┬──────┘        └──────┬──────┘
          │                      │
   ┌──────▼──────────────────────▼──────┐
   │          product.py                │
   │  Selenium + BS4 + undetected-      │
   │  chromedriver dual-platform scraper│
   └──────────────────┬─────────────────┘
                      │
   ┌──────────────────▼─────────────────┐
   │           matcher.py               │
   │  Cross-platform product pairing    │
   │  and brand extraction              │
   └──────┬───────────────────┬─────────┘
          │                   │
 ┌────────▼───┐       ┌───────▼──────┐
 │selection.py│       │forecasting.py│
 │top-K score │       │Holt-Winters  │
 └────────────┘       └──────────────┘
          │                   │
   ┌──────▼───────────────────▼──────────┐
   │           dashboard.py              │
   │  Dark trading-terminal Streamlit UI │
   │  • Free-text search + live indexing │
   │  • Appliance drill-down (AC, Fridge)│
   │  • Brand drill-down (Phones/Laptops)│
   │  • Real sentiment from review CSVs  │
   │  • Dynamic price drop feed          │
   └─────────────────────────────────────┘
```

**Orchestrator:** `pipeline.py` chains all steps end-to-end per category.

---

## 🚀 Features

| Feature | Details |
|---|---|
| **Dual-platform tracking** | Flipkart vs Amazon comparison per product with winner badge |
| **3 categories** | Mobiles, Laptops, Home Appliances (extensible via `config/categories.py`) |
| **Live on-demand search** | Recognised queries not in catalog get market-estimate pricing indexed automatically |
| **Meaningful-query guard** | Random text / typos are NOT auto-indexed — query must match a known brand or product keyword |
| **Appliance category drill-down** | Filter Home Appliances by item type (❄️ AC, 🧊 Fridge, 🫧 Washing Machine, 📡 Microwave, etc.) instead of brand names |
| **Brand drill-down** | Dynamic multiselect per brand for Mobiles & Laptops (Apple, Samsung, Dell, HP, Lenovo, etc.) |
| **Holt-Winters forecasting** | 7-day forecast with confidence bands and MAPE accuracy tracking |
| **Real sentiment analysis** | Actual review text + sentiment labels from CSV; falls back to category-generic snippets only when no real data exists |
| **Dynamic price drop feed** | Computed live from `(MRP - price) / MRP` across all visible products |
| **Watchlist** | Star any product to pin it across sessions |
| **Direct links** | Clickable "Buy on Flipkart / Amazon" per product |

---

## 📂 Project Structure

```
infosys_internship/
├── core/                                # Domain business logic & typed models
│   ├── __init__.py
│   ├── models.py                        # Strongly-typed dataclasses (ProductItem, CompetitorPair, etc.)
│   ├── brands.py                        # Brand normalization & canonical casing
│   ├── appliances.py                    # Appliance taxonomy, rules & spec extractors
│   ├── analytics.py                     # Holt-Winters forecasting, sentiment & price drops
│   └── data_loader.py                   # Multi-category CSV loading, sanitization & indexing
├── ui/                                  # Modular Streamlit Trading Terminal UI
│   ├── __init__.py
│   ├── styles.py                        # Terminal CSS, custom typography & pulse animations
│   ├── common.py                        # Compatibility wrappers (safe_button, render_plotly)
│   ├── charts.py                        # Plotly builders (sparklines, divergence, sentiment)
│   └── components/                      # Modular UI components
│       ├── __init__.py
│       ├── topbar.py                    # Terminal header & live status strip
│       ├── controls.py                  # Search, category dropdown & dynamic drilldowns
│       ├── kpis.py                      # 4-card metric strip (Parity, Volatility, etc.)
│       ├── price_feed.py                # Chronological price drop feed expander
│       ├── product_card.py              # Visual product cards with winner badges & links
│       └── detail_view.py               # Asset inspection view with Arbitrage Calculator
├── tests/                               # Comprehensive unit test suite
│   ├── __init__.py
│   ├── test_models.py                   # Tests for dataclass calculations & arbitrage edge
│   ├── test_appliances.py               # Tests for AC, Fridge, Washer & spec extraction
│   ├── test_brands.py                   # Tests for canonical casing & normalization
│   ├── test_analytics.py                # Tests for Holt-Winters, MAPE, and search query engine
│   └── run_all_tests.py                 # Test runner script
├── config/
│   ├── __init__.py
│   └── categories.py                    # Per-category scraping config
├── data/
│   ├── price_history.csv                # Append-only time-series prices
│   ├── mobiles_matched_products.csv
│   ├── laptops_matched_products.csv
│   ├── home_appliances_matched_products.csv
│   ├── reviews_with_sentiment.csv       # Real reviews with sentiment labels
│   ├── *_forecasts.csv                  # Holt-Winters forecasts per category
│   └── *_top_products.csv               # Top-K scored products per category
├── product.py                           # Dual-platform Flipkart + Amazon scraper
├── matcher.py                           # Product matching & brand extraction
├── ingestion.py                         # Data cleaning and normalization
├── selection.py                         # Product scoring and top-K selection
├── forecasting.py                       # Holt-Winters price forecasting CLI + MAPE
├── sentiment.py                         # Sentiment analysis
├── pipeline.py                          # End-to-end orchestrator (CLI + importable)
├── main.py                              # Entry point (delegates to pipeline.py)
├── dashboard.py                         # Lean orchestrator for Streamlit dark terminal UI
├── env/.env                             # Environment variables (gitignored)
├── requirements.txt
├── CHANGELOG.md
└── readme.md
```

---

## 📦 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Madhu-0007/infosys_internship.git
   cd infosys_internship
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate # macOS/Linux
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp env/.env.example env/.env
   # Fill in your API keys / credentials
   ```

---

## ▶️ Usage

### Launch the dashboard

```bash
streamlit run dashboard.py
```

| Search query | Behaviour |
|---|---|
| Product already in catalog | Shown immediately with real data |
| Recognised new product (known brand/keyword) | Market-estimated pricing generated and indexed |
| Random text / unrecognised query | No auto-indexing — shows "no results" cleanly |

### Run the scraping pipeline (CLI)

```bash
python pipeline.py --category mobiles   # single category
python pipeline.py --all                # all categories
```

### Add a new category

1. Add an entry to [`config/categories.py`](config/categories.py) with URL templates and CSS selectors.
2. Add the slug to `ALL_SUPPORTED_CATEGORIES` in `dashboard.py`.
3. Restart the dashboard.

### Run unit tests

```bash
python tests/run_all_tests.py
# or with unittest discovery:
python -m unittest discover -s tests -p "test_*.py"
```

---


## 🏠 Home Appliances: Item Category Drill-Down & Grouping

Instead of company names (LG, Samsung, Bosch, etc.), Home Appliances uses appliance categories for both drill-down filtering and card grouping:

| Category | Keyword signals |
|---|---|
| ❄️ Air Conditioners (AC) | "split ac", " ac ", "air conditioner", "inverter ac", "1.5 ton" |
| 🧊 Refrigerators (Fridge) | "refrigerator", "fridge", "double door", "frost free", "direct cool" |
| 🫧 Washing Machines | "washing machine", "front load", "top load", "fully automatic" |
| 📡 Microwaves & Ovens | "microwave", "convection", "solo oven", "oven", "tandoor" |
| 📺 Televisions (TV) | "television", " tv ", "smart tv", "oled", "qled", "led tv", "4k tv" |
| 💧 Water Purifiers | "water purifier", "ro purifier", "uv purifier" |
| 🌀 Air Purifiers | "air purifier", "hepa filter", "air cleaner" |
| 🔥 Geysers & Heaters | "geyser", "water heater", "room heater" |
| 🍳 Kitchen Appliances | "chimney", "mixer", "induction", "kettle", "blender" |
| 🌬️ Fans & Coolers | "ceiling fan", "air cooler", "desert cooler", "tower fan" |
| 🧹 Vacuum Cleaners | "vacuum cleaner", "robot vacuum" |
| 🏠 Other Appliances | everything else |

Within each section, individual cards show product brands (LG, Samsung, Whirlpool, etc.), specifications, and Flipkart vs. Amazon live prices.

---

## ⚠️ Anti-Bot Hardening

- `undetected-chromedriver` (stealth Selenium)
- Randomized inter-page delays
- Rotating User-Agent strings
- Exponential backoff retry on failures
- Graceful category skip on persistent failure

---

## 🤝 Contributing

Fork the repository and submit a pull request. Contributions are welcome!

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

---

## 👤 Contact
Developed by [Madhu-0007](https://github.com/Madhu-0007).

