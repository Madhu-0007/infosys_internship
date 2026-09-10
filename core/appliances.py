"""
core/appliances.py — Classification rules and specification extractors for Home Appliances & Electronics.
"""
import re
from typing import List, Tuple, Dict


# Ordered appliance type definitions — order determines display priority
_APPLIANCE_TYPE_RULES: List[Tuple[str, str, List[str]]] = [
    ("❄️ Air Conditioners (AC)",   "ac",       ["split ac", " ac ", "air conditioner", "inverter ac", "ton ac", "1.5 ton", "1 ton", "2 ton", "window ac"]),
    ("🧊 Refrigerators (Fridge)",  "fridge",   ["refrigerator", "fridge", "double door", "triple door", "single door", "frost free", "direct cool"]),
    ("🫧 Washing Machines",        "washer",   ["washing machine", "front load", "top load", "washer", "dryer", "fully automatic", "semi automatic"]),
    ("📡 Microwaves & Ovens",      "microwave",["microwave", "convection", "solo oven", "grill oven", "oven", "tandoor"]),
    ("📺 Televisions (TV)",        "tv",       ["television", " tv ", "smart tv", "oled", "qled", "led tv", "4k tv", "8k tv"]),
    ("💧 Water Purifiers",         "purifier", ["water purifier", "ro purifier", "uv purifier", "purifier"]),
    ("🌀 Air Purifiers",           "airpur",   ["air purifier", "hepa filter", "air cleaner"]),
    ("🔥 Geysers & Heaters",       "heater",   ["geyser", "water heater", "room heater", "storage heater", "instant heater"]),
    ("🍳 Kitchen Appliances",      "kitchen",  ["chimney", "mixer", "grinder", "blender", "juicer", "food processor", "induction", "kettle", "toaster", "sandwich"]),
    ("🌬️ Fans & Coolers",          "fan",      ["ceiling fan", "table fan", "pedestal fan", "air cooler", "desert cooler", "tower fan"]),
    ("🧹 Vacuum Cleaners",         "vacuum",   ["vacuum cleaner", "wet dry vacuum", "robot vacuum", "floor cleaner"]),
    ("🏠 Other Appliances",        "other",    []),  # catch-all
]


def get_appliance_type(product_name: str) -> str:
    """
    Classifies a home appliance product into a display category based on
    keyword matching against the product title.
    Returns the emoji+label string used as the section header and drill-down in the dashboard.
    """
    t = f" {product_name.lower()} "
    for label, _slug, keywords in _APPLIANCE_TYPE_RULES:
        if not keywords:  # catch-all
            return label
        for kw in keywords:
            if kw in t:
                return label
    return "🏠 Other Appliances"


def get_department_name(category: str) -> str:
    """Classifies a category into either 'Appliances' or 'Gadgets'."""
    norm = str(category).lower().strip().replace("-", "_").replace(" ", "_")
    if norm in ["home_appliances", "appliances"]:
        return "🧺 HOME APPLIANCES"
    return "💻📱 GADGETS & CONSUMER ELECTRONICS"


def extract_generic_specs(title: str, category_hint: str = "") -> Dict[str, str]:
    """
    Extracts generic key-value specification badges without hardcoded schemas.
    Handles appliances (Capacity, RPM, Stars, Inverter) and electronics (RAM, CPU, Storage).
    """
    t_lower = str(title).lower()
    specs: Dict[str, str] = {}

    # Appliances
    cap_kg = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:kg|k\.g\.)\b", t_lower)
    cap_litres = re.search(r"\b(\d+)\s*(?:l|litres?|liter)\b", t_lower)
    cap_ton = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:ton)\b", t_lower)
    if cap_kg:
        specs["Capacity"] = f"{cap_kg.group(1)} kg"
    elif cap_litres:
        specs["Capacity"] = f"{cap_litres.group(1)} L"
    elif cap_ton:
        specs["Capacity"] = f"{cap_ton.group(1)} Ton"

    rpm = re.search(r"\b(\d{3,4})\s*(?:rpm)\b", t_lower)
    if rpm:
        specs["Speed"] = f"{rpm.group(1)} RPM"

    stars = re.search(r"\b([1-5])\s*(?:star|\*)\b", t_lower)
    if stars:
        specs["Energy"] = f"{stars.group(1)}★ Star"

    if "front load" in t_lower:
        specs["Type"] = "Front Load"
    elif "top load" in t_lower:
        specs["Type"] = "Top Load"
    elif "double door" in t_lower:
        specs["Type"] = "Double Door"
    elif "triple door" in t_lower:
        specs["Type"] = "Triple Door"
    elif "split ac" in t_lower:
        specs["Type"] = "Split AC"
    elif "convection" in t_lower:
        specs["Type"] = "Convection"

    if "inverter" in t_lower:
        specs["Tech"] = "Inverter"

    # Electronics
    ram = re.search(r"\b(4|6|8|12|16|24|32|64)\s*(?:gb|g)\s*(?:ddr\d|lpddr\d|ram)?\b", t_lower)
    if ram and "Capacity" not in specs:
        specs["RAM"] = f"{ram.group(1)} GB"

    storage_tb = re.search(r"\b(1|2)\s*(?:tb)\b", t_lower)
    storage_gb = re.search(r"\b(64|128|256|512)\s*(?:gb)\s*(?:ssd|emmc|rom|storage)?\b", t_lower)
    if storage_tb:
        specs["Storage"] = f"{storage_tb.group(1)} TB"
    elif storage_gb and ("RAM" in specs and specs["RAM"] != f"{storage_gb.group(1)} GB"):
        specs["Storage"] = f"{storage_gb.group(1)} GB"

    cpu = re.search(r"\b(i3|i5|i7|i9|ryzen\s*[3579]|m1|m2|m3|m4|celeron|kompanio|snapdragon\s*x?)\b", t_lower)
    if cpu:
        specs["Processor"] = cpu.group(1).upper()

    return specs
