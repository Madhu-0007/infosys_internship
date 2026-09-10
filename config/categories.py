"""
config/categories.py — Per-category scraping configuration for Flipkart & Amazon.

Each category defines:
  - search_url_template (Flipkart)
  - listing_selectors & review_selectors (Flipkart)
  - amazon_search_url_template (Amazon)
  - amazon_selectors (Amazon)
  - quirks: category-specific notes or adjustments
"""

CATEGORIES = {
    "mobiles": {
        "search_url_template": "https://www.flipkart.com/search?q=mobiles&page={}",
        "listing_selectors": {
            "product_container": {"tag": "div", "attrs": {"data-id": True}},
            "title": {"tag": "div", "attrs": {"class": "RG5Slk"}},
            "price": {"tag": "div", "attrs": {"class": "hZ3P6w"}},
            "mrp": {"tag": "div", "attrs": {"class": "kRYCnD"}},
            "discount": {"tag": "div", "attrs": {"class": "HQe8jr"}},
            "rating": {"tag": "div", "attrs": {"class": "XQDdHH"}},
            "link": {"tag": "a", "attrs": {"class": "k7wcnx"}},
        },
        "review_selectors": {
            "page_loaded": "VU-ZEz",
            "review_container": {"tag": "div", "attrs": {"class": "cPHDOP"}},
            "user": {"tag": "p", "attrs": {"class": "_2NsDsF AwS1CA"}},
            "rating": {"tag": "div", "attrs": {"class": "_3LWZlK"}},
            "text": {"tag": "div", "attrs": {"class": "ZmyHeo"}},
            "date_paragraphs": {"tag": "p", "attrs": {"class": "_2NsDsF"}},
        },
        "amazon_search_url_template": "https://www.amazon.in/s?k=mobiles&page={}",
        "amazon_selectors": {
            "product_container": {"tag": "div", "attrs": {"data-component-type": "s-search-result"}},
            "title": {"tag": "h2", "attrs": {}},
            "price": {"tag": "span", "attrs": {"class": "a-price-whole"}},
            "mrp": {"tag": "span", "attrs": {"class": "a-price a-text-price"}},
            "rating": {"tag": "span", "attrs": {"class": "a-icon-alt"}},
            "link": {"tag": "a", "attrs": {"class": "a-link-normal s-no-outline"}},
        },
        "quirks": "Mobile-specific: check storage capacity (64GB/128GB/256GB) for accurate matching.",
    },

    "laptops": {
        "search_url_template": "https://www.flipkart.com/search?q=laptops&page={}",
        "listing_selectors": {
            "product_container": {"tag": "div", "attrs": {"data-id": True}},
            "title": {"tag": "div", "attrs": {"class": "RG5Slk"}},
            "price": {"tag": "div", "attrs": {"class": "hZ3P6w"}},
            "mrp": {"tag": "div", "attrs": {"class": "kRYCnD"}},
            "discount": {"tag": "div", "attrs": {"class": "HQe8jr"}},
            "rating": {"tag": "div", "attrs": {"class": "XQDdHH"}},
            "link": {"tag": "a", "attrs": {"class": "k7wcnx"}},
        },
        "review_selectors": {
            "page_loaded": "VU-ZEz",
            "review_container": {"tag": "div", "attrs": {"class": "cPHDOP"}},
            "user": {"tag": "p", "attrs": {"class": "_2NsDsF AwS1CA"}},
            "rating": {"tag": "div", "attrs": {"class": "_3LWZlK"}},
            "text": {"tag": "div", "attrs": {"class": "ZmyHeo"}},
            "date_paragraphs": {"tag": "p", "attrs": {"class": "_2NsDsF"}},
        },
        "amazon_search_url_template": "https://www.amazon.in/s?k=laptops&page={}",
        "amazon_selectors": {
            "product_container": {"tag": "div", "attrs": {"data-component-type": "s-search-result"}},
            "title": {"tag": "h2", "attrs": {}},
            "price": {"tag": "span", "attrs": {"class": "a-price-whole"}},
            "mrp": {"tag": "span", "attrs": {"class": "a-price a-text-price"}},
            "rating": {"tag": "span", "attrs": {"class": "a-icon-alt"}},
            "link": {"tag": "a", "attrs": {"class": "a-link-normal s-no-outline"}},
        },
        "quirks": "Laptop listings often have longer titles with spec details.",
    },

    "home_appliances": {
        "search_url_template": "https://www.flipkart.com/search?q=home+appliances&page={}",
        "listing_selectors": {
            "product_container": {"tag": "div", "attrs": {"data-id": True}},
            "title": {"tag": "div", "attrs": {"class": "RG5Slk"}},
            "price": {"tag": "div", "attrs": {"class": "hZ3P6w"}},
            "mrp": {"tag": "div", "attrs": {"class": "kRYCnD"}},
            "discount": {"tag": "div", "attrs": {"class": "HQe8jr"}},
            "rating": {"tag": "div", "attrs": {"class": "XQDdHH"}},
            "link": {"tag": "a", "attrs": {"class": "k7wcnx"}},
        },
        "review_selectors": {
            "page_loaded": "VU-ZEz",
            "review_container": {"tag": "div", "attrs": {"class": "cPHDOP"}},
            "user": {"tag": "p", "attrs": {"class": "_2NsDsF AwS1CA"}},
            "rating": {"tag": "div", "attrs": {"class": "_3LWZlK"}},
            "text": {"tag": "div", "attrs": {"class": "ZmyHeo"}},
            "date_paragraphs": {"tag": "p", "attrs": {"class": "_2NsDsF"}},
        },
        "amazon_search_url_template": "https://www.amazon.in/s?k=home+appliances&page={}",
        "amazon_selectors": {
            "product_container": {"tag": "div", "attrs": {"data-component-type": "s-search-result"}},
            "title": {"tag": "h2", "attrs": {}},
            "price": {"tag": "span", "attrs": {"class": "a-price-whole"}},
            "mrp": {"tag": "span", "attrs": {"class": "a-price a-text-price"}},
            "rating": {"tag": "span", "attrs": {"class": "a-icon-alt"}},
            "link": {"tag": "a", "attrs": {"class": "a-link-normal s-no-outline"}},
        },
        "quirks": "Home appliances have diverse sub-categories; search results may mix types.",
    },
}

# Default scraping parameters (overridable via env vars)
DEFAULT_LISTING_PAGES = 5
DEFAULT_REVIEW_PAGES = 2
DEFAULT_OUTPUT_DIR = "data"
