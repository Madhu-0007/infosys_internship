# CHANGELOG

All notable changes to the E-Commerce Competitor Intelligence Pipeline.

---

## [2.0.0] — Multi-Category Restructure

### Phase 0 — Audit & Cleanup

**Removed:**
- `predict_price_lgbm()` function from `dashboard.py` — this was a same-day
  proxy model (LightGBM predicting current price from discount+rating), NOT
  real forecasting. Replaced by `forecasting.py` time-series approach.
- Unused imports from `dashboard.py`: `joblib`, `TextBlob`, `sys`, `shutil`,
  `subprocess`, `time`
- Old `main.py` — was an unrelated Groq API test (`client.chat.completions`)
  with no connection to the pipeline
- `orchestrate_pipeline()`, `run_script()`, `rotate_snapshots()` from
  `dashboard.py` — moved to `pipeline.py` (decoupling dashboard from pipeline)
- Placeholder comment `# ...existing code...` in `dashboard.py`

**Fixed:**
- `My_docs` vs `my_docs` path bug in `notification.py` — was already fixed
  in a previous iteration; confirmed no remaining case issues

**Added:**
- `.gitignore` extended with `__pycache__/`, `*.pyc`, `*.pyo`, `.env`, `*.joblib`
- `.env.example` listing all required environment variables

---

### Phase 1 — Category-Driven Config (previously completed)

- `config/categories.py` defines mobiles, laptops, home_appliances
- Each category has search URL template, listing selectors, review selectors
- `product.py` accepts `--category` parameter and loads selectors from config

---

### Phase 2 — Anti-Bot Hardening (previously completed)

- `product.py` uses `undetected-chromedriver` with fallback to plain Selenium
- Randomized delays (2–6s), rotating User-Agent pool (6 strings)
- Retry with exponential backoff on page load failures
- Graceful degradation: failed categories are skipped, not fatal

---

### Phase 3 — Time-Series Data Model (previously completed)

- Append-only `data/price_history.csv` with schema:
  productid, category, product_name, source, price, mrp, discount, rating, scraped_at
- Snapshot mechanism (`my_docs/mobile_yesterday.csv`) kept for notification.py
  diff logic — simpler than deriving "yesterday's price" from history file

---

### Phase 4 — Product Selection (previously completed)

- `selection.py` with composite scoring: review_count (40%) + price_volatility (60%)
- Min 3 history points before volatility is meaningful
- Top-K (default 20) products per category for deep tracking
- Saves to `data/{category}_top_products.csv`

---

### Phase 5 — Real Forecasting (completed in this restructure)

**Removed:**
- Old LightGBM price prediction from `dashboard.py` (was not real forecasting)

**Added:**
- `forecasting.py` — Simple Exponential Smoothing with trend extrapolation
- Requires 5+ data points; shows "insufficient history" otherwise
- Outputs: current_price, predicted_price_7d, trend (up/down/flat), confidence
- Clear extension point for Prophet/ARIMA when data supports it
- Dashboard now displays forecast results with trend emoji and confidence

---

### Phase 6 — Decouple Dashboard from Pipeline

**Changed:**
- Dashboard no longer auto-runs the entire pipeline on first session load
- Dashboard is read-only by default — loads latest CSV data
- Added category selector (sidebar) — switch between mobiles/laptops/etc.
- Added "🔄 Refresh Data" button — triggers pipeline per category on demand
- `CompetitorAnalyzer.load_data()` now accepts `category` parameter
- Per-category data loading with fallback to legacy paths

---

### Phase 7 — Orchestration

**Added:**
- `pipeline.py` — end-to-end orchestrator:
  scrape → ingest → select → forecast → sentiment → notify
- CLI support: `python pipeline.py --category mobiles` or `--all`
- Callable from dashboard via `import pipeline; pipeline.main(category=...)`
- Each step wrapped in try/except for graceful degradation

**Changed:**
- `main.py` — now delegates to `pipeline.py` (was Groq API test)
- `ingestion.py` — `main()` accepts `category` parameter, dynamic paths
- `sentiment.py` — top-level script wrapped in `main(category=None)` function

---

### Phase 8 — Documentation

**Added:**
- Rewrote `README.md` with actual architecture (ASCII diagram), no RAG mentions
- Created `.env.example` with all required environment variables
- Created this `CHANGELOG.md`
