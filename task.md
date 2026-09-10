# TASK: Restructure E-Commerce Competitor Intelligence Pipeline (Multi-Category)

You are a senior Python engineer. You are rebuilding an existing repo
(originally a single-category, mobiles-only Flipkart scraper +
dashboard project). Follow this checklist IN ORDER. Do not skip
steps. Do not invent scope beyond what's listed. Ask nothing — make
reasonable engineering decisions and document them briefly in code
comments/CHANGELOG.md instead of asking the user, EXCEPT where this
document explicitly tells you to make a decision visible and
documented rather than silent.

## CONTEXT
- Current repo has: product.py (Selenium+BS4 scraper, mobiles only,
  hardcoded CSS selectors, gets blocked by bot detection, runs at
  import time with no `main()` guard), ingestion.py (cleaning + a
  same-day proxy "price prediction" model that is NOT real
  forecasting; has an unused `TextBlob` import and a `valid_product_ids`
  unbound-variable bug when the mobile file is missing), sentiment.py
  (OpenAI sentiment, works fine, keep; also runs at import time),
  notification.py (email alerts; has a path bug using `My_docs/`
  instead of `my_docs/` — check ALL occurrences, there may be more
  than two), login.py (Supabase auth, keep as-is), dashboard.py
  (Streamlit, currently auto-runs the ENTIRE pipeline including paid
  OpenAI calls on every fresh session load — this must be decoupled;
  also contains a fake LightGBM price "prediction"), main.py (a Groq
  API test script, unrelated to the pipeline — dead code).
- Goal: generalize from mobiles-only to multiple product categories,
  fix bot detection, select only high-value products per category
  instead of tracking everything, and replace the fake "prediction"
  with real time-series forecasting.

## PHASE 0 — AUDIT & CLEANUP (do this first)
- [ ] Read every .py file in the repo fully before changing anything.
- [ ] Identify and DELETE dead code, unused imports, commented-out
      blocks, and duplicate logic. List what you removed in a
      CHANGELOG.md.
- [ ] DELETE main.py (Groq API test script, not part of the pipeline).
- [ ] Fix the `My_docs` vs `my_docs` path bug in notification.py —
      check every line, not just the first occurrence you find.
- [ ] Fix the `valid_product_ids` unbound-variable bug in ingestion.py
      (referenced in the reviews section even if the mobile file is
      missing).
- [ ] Remove the unused `TextBlob` import in ingestion.py.
- [ ] Wrap the top-level scraping code in product.py, and the
      top-level sentiment code in sentiment.py, in `main()` functions
      so neither executes on import (required for pipeline.py to
      import them safely in later phases).
- [ ] Remove debug `print()` statements not needed for real logging.
- [ ] Update `.gitignore` to add `__pycache__/`, `*.pyc`, `*.joblib`,
      `notifier.log` (in addition to the existing `/env` entry).
- [ ] Confirm .env is gitignored (it already is) — do not touch
      secrets handling logic, only reference env vars the same way
      existing code does.
- [ ] Do NOT touch or attempt to build any RAG/FAISS/LangChain code —
      explicitly out of scope for this task.

## PHASE 1 — CATEGORY-DRIVEN CONFIG
- [ ] Create a single `config/categories.py` (a Python dict is fine —
      simpler than YAML, no extra dependency) defining, per category
      (start with: mobiles, laptops, home_appliances — extensible
      later):
      - search URL template
      - CSS selectors for listing (title, price, mrp, discount,
        rating, link) and review page selectors
      - any category-specific quirks
- [ ] **Only `mobiles` has verified, real CSS selectors** — these
      already exist in the current product.py, reverse-engineered
      from live Flipkart HTML. For `laptops` and `home_appliances`,
      insert clearly marked PLACEHOLDER selectors with a
      `# TODO: verify against live Flipkart HTML — not yet confirmed`
      comment. Do NOT invent or guess plausible-looking Flipkart CSS
      class names for these categories — fabricated selectors that
      merely look plausible will silently return 0 products and waste
      debugging time later. If you have live browser access and can
      genuinely inspect Flipkart's laptop/appliance listing pages,
      you may fill in real selectors instead of placeholders — but do
      not simulate or guess this from training knowledge alone.
- [ ] Refactor product.py so it takes `--category` as a CLI parameter
      and loads selectors from this config instead of hardcoding
      Flipkart mobile-specific class names inline.
- [ ] Add a 0-product sentinel check: if a listing page returns 0
      products, log a clear ERROR (not a silent empty result) naming
      the category and which selector likely broke or was a
      placeholder.

## PHASE 2 — ANTI-BOT-DETECTION HARDENING
- [ ] Replace plain Selenium with `undetected-chromedriver` (or an
      equivalent free stealth approach you judge best) to reduce bot
      detection.
- [ ] Pin `undetected-chromedriver` to a specific compatible version
      range in requirements.txt — do not add it unpinned. This
      library has a history of breaking changes tied to Chrome
      version bumps, and an unpinned install can silently stop
      working after a routine `pip install -r requirements.txt` on a
      machine with a newer Chrome.
- [ ] Add randomized delays between requests/pages (uniform random
      between bounds, not a fixed `time.sleep(WAIT)`), randomized or
      rotating User-Agent strings, and basic retry-with-exponential-
      backoff on failed page loads.
- [ ] Add graceful degradation: if a category scrape fails
      repeatedly, log and skip it rather than crashing the whole run.
- [ ] Document in README.md that this is a best-effort free approach
      and may still need paid proxy rotation later if blocking
      persists — do not imply this fully solves bot detection.

## PHASE 3 — TIME-SERIES DATA MODEL (replaces snapshot diffing)
- [ ] Design and implement an append-only `data/price_history.csv`
      (or per-category files — your call, document which in
      CHANGELOG.md) with schema:
      `productid, category, product_name, source, price, mrp,
      discount, rating, scraped_at`
- [ ] Every scrape run APPENDS new rows (never overwrites), so each
      product accumulates real price history over time.
- [ ] **Decision to make and document, not skip silently**: decide
      whether to keep the existing yesterday/today snapshot mechanism
      for notification.py's diff logic, or derive "yesterday's price"
      from price_history.csv instead. Pick whichever is simpler and
      more robust for now — but explicitly write in CHANGELOG.md:
      (a) which you chose and why, and (b) if you kept both snapshot
      files AND price_history.csv, flag this as **known duplication /
      two sources of truth for price data**, to be revisited once
      price_history.csv has enough accumulated depth to safely
      replace snapshot diffing entirely. Do not leave this
      undocumented.
- [ ] **State explicitly in CHANGELOG.md** whether any existing
      historical data (`data/cleaned_mobile.csv`,
      `reviews_with_sentiment.csv`) is migrated into the new
      price_history.csv schema, or whether tracking starts from zero
      for all categories going forward. Do not decide this silently —
      pick one, document why, and note the practical consequence
      (e.g., "forecasting will show 'insufficient history' for all
      products until N days of new scraping accumulate" if starting
      from zero).

## PHASE 4 — PRODUCT SELECTION / SCORING (new module)
- [ ] Create `selection.py`. Per category, compute per product:
      - `review_count` from reviews data
      - `price_volatility = std(price) / mean(price)` across all
        historical scrapes for that product, from price_history.csv
        (guard against division by zero / insufficient history — need
        a minimum N data points, e.g. 3, before volatility is
        meaningful; fall back to review_count-only ranking until then)
      - `composite_score` = a weighted combination of normalized
        review_count and normalized price_volatility (pick sensible
        default weights; make them configurable constants —
        `WEIGHT_REVIEWS`, `WEIGHT_VOLATILITY`, `MIN_HISTORY_POINTS`,
        `TOP_K`, not hardcoded magic numbers inline)
- [ ] Select top-K (configurable, default e.g. 20) products per
      category by composite_score.
- [ ] Only these top-K products should get deep tracking (reviews +
      forecasting) going forward — this is a cost/relevance filter,
      not a hard exclusion of scraping other products for price-only
      snapshots if cheap to keep.

## PHASE 5 — REAL FORECASTING (replaces train_price_model_lgbm)
- [ ] DELETE the current same-day proxy model
      (`train_price_model_lgbm()` in ingestion.py, which predicts
      current price from discount+rating — this is not forecasting).
- [ ] Explicitly DELETE the generated file
      `data/price_predictor_lgbm.joblib` itself, not just the code
      that references it — a stale file with a mismatched schema
      lying around can cause confusing bugs later.
- [ ] Remove `predict_price_lgbm()` and the `import joblib` from
      dashboard.py as part of this phase (coordinate with Phase 6).
- [ ] Build real per-product time-series forecasting using
      price_history.csv, in a new `forecasting.py`:
      - Require a minimum history length (e.g. 5+ data points) before
        forecasting a product; otherwise return/display "insufficient
        history" rather than a fake number.
      - Start with a robust simple baseline — Simple Exponential
        Smoothing (via `statsmodels`) or an equivalent simple,
        well-understood method. Do NOT over-engineer with heavy
        models until enough real data exists to validate against.
      - Leave a clear, documented extension point to swap in Prophet
        or similar later once sufficient history accumulates — don't
        build that now if the data won't support it yet.
      - Output per product: `current_price`, `predicted_price_7d`,
        `trend` (up/down/flat), and a `confidence` indicator (e.g.
        low/medium/high based on history length and volatility).
      - Save forecasts to `data/forecasts.csv`.
- [ ] Update requirements.txt: add `statsmodels`, remove `lightgbm`
      (no longer used).

## PHASE 6 — DECOUPLE DASHBOARD FROM PIPELINE
- [ ] Remove the auto-run-entire-pipeline-on-first-load behavior in
      dashboard.py's `main()`.
- [ ] Dashboard should be read-only by default: load latest processed
      CSVs (including `data/forecasts.csv`) and display them.
- [ ] Add an explicit "Refresh Data" button/action in the sidebar,
      with a category selector dropdown, so the user can refresh one
      category at a time instead of always running all. Clicking
      Refresh triggers `pipeline.py --category <selected>`.
- [ ] Update product analysis view to show real forecast data
      (current price, predicted +7d price, trend, confidence, or
      "insufficient history") instead of the removed LightGBM
      prediction.
- [ ] Add category filter → product selection scoped to that
      category's top-K list from selection.py.

## PHASE 7 — ORCHESTRATION
- [ ] Create a single `pipeline.py` that runs the full flow
      end-to-end per category:
      `scrape → ingest/clean → append to price_history → score/select
      top-K → forecast → sentiment (top-K only) → notify`
- [ ] Make it runnable both as a CLI (`python pipeline.py --category
      mobiles` or `--all`) and callable from the dashboard's Refresh
      button (via subprocess or direct import — your call).
- [ ] Proper error handling and logging per step — one category's
      failure should not silently abort other categories in `--all`
      mode.

## PHASE 8 — DOCS
- [ ] Rewrite README.md to reflect the ACTUAL current architecture
      (no RAG/FAISS/LangChain mention — that's explicitly not
      implemented and out of scope). Include an ASCII architecture
      diagram, setup instructions, and a `config/categories.py`
      example. Clearly note in README which categories have verified
      selectors (mobiles) vs. placeholders needing manual
      verification (laptops, home_appliances).
- [ ] Add `.env.example` listing all required env vars with
      placeholder values (no real secrets).
- [ ] Finalize CHANGELOG.md: a complete summary of everything removed,
      added, and why, across every phase — including the two explicit
      decisions this document required you to document (Phase 3's
      snapshot-vs-price_history choice, and the historical-data
      migration-vs-fresh-start choice).

## CONSTRAINTS
- Keep sentiment.py and login.py logic as-is except for the specific
  bug/structure fixes listed in Phase 0 — do not rewrite what already
  works.
- Do not add paid proxy services or paid APIs beyond what's already
  used (OpenAI for sentiment).
- Do not implement RAG/FAISS/LangChain — explicitly excluded.
- Do not fabricate CSS selectors for categories you cannot verify —
  use placeholders as instructed in Phase 1.
- Prioritize correctness and clarity over cleverness — this must be
  maintainable by the original author, a student, not just readable
  by an expert.
- After each phase, run the affected script(s) to confirm they at
  least execute without crashing before moving to the next phase.

  this supersedes the previous task.md, start from Phase 0."