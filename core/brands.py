"""
core/brands.py — Canonical brand mapping and normalization utilities.
"""
import re
from typing import Any


def normalize_str(s: Any) -> str:
    """Safely lowercases and strips strings."""
    if s is None or not isinstance(s, str):
        return ""
    return re.sub(r"\s+", " ", s.lower().strip())


def canonical_brand_name(brand: Any) -> str:
    """
    Returns clean, professional brand casing for headers and company chips.
    Guarantees 'lg', 'LG', ' LG ' all resolve to 'LG'.
    """
    norm = normalize_str(brand)
    casing_map = {
        "lg": "LG",
        "hp": "HP",
        "asus": "ASUS",
        "msi": "MSI",
        "ifb": "IFB",
        "iqoo": "iQOO",
        "apple": "Apple",
        "iphone": "Apple",
        "ipad": "Apple",
        "macbook": "Apple",
        "samsung": "Samsung",
        "galaxy": "Samsung",
        "dell": "Dell",
        "lenovo": "Lenovo",
        "acer": "Acer",
        "whirlpool": "Whirlpool",
        "haier": "Haier",
        "bosch": "Bosch",
        "godrej": "Godrej",
        "voltas": "Voltas",
        "daikin": "Daikin",
        "motorola": "Motorola",
        "moto": "Motorola",
        "realme": "Realme",
        "xiaomi": "Xiaomi",
        "redmi": "Redmi",
        "oneplus": "OnePlus",
        "vivo": "Vivo",
        "oppo": "OPPO",
        "poco": "POCO",
        "philips": "Philips",
        "primebook": "Primebook",
        "infinix": "Infinix",
        "honor": "Honor",
        "cmf": "CMF by Nothing",
        "nothing": "Nothing",
        "sony": "Sony",
        "google": "Google",
        "pixel": "Google",
    }
    if norm in casing_map:
        return casing_map[norm]
    return norm.title() if norm else "Unknown Brand"


def normalize_category(cat: Any) -> str:
    """
    Normalizes category inputs into canonical slugs:
    'laptops', 'mobiles', 'home_appliances', or 'all'.
    """
    norm = normalize_str(cat).replace(" ", "_").replace("-", "_")
    if norm in ["home_appliances", "homeappliances", "appliances", "appliance", "home_appliance", "home"]:
        return "home_appliances"
    if norm in ["mobiles", "mobile", "smartphones", "smartphone", "phones", "phone"]:
        return "mobiles"
    if norm in ["laptops", "laptop", "notebooks", "notebook", "computers", "pc"]:
        return "laptops"
    if norm in ["all", "all_categories", "all_category", "allcategories", "*"]:
        return "all"
    return norm

