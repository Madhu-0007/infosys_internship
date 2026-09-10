"""
tests/test_brands.py — Unit tests for brand name casing, normalization, and category resolution.
"""
import unittest

from core.brands import (
    canonical_brand_name,
    normalize_str,
    normalize_category,
)


class TestBrandNormalization(unittest.TestCase):
    def test_canonical_casing(self):
        self.assertEqual(canonical_brand_name("lg"), "LG")
        self.assertEqual(canonical_brand_name("hp"), "HP")
        self.assertEqual(canonical_brand_name("asus"), "ASUS")
        self.assertEqual(canonical_brand_name("apple"), "Apple")
        self.assertEqual(canonical_brand_name("samsung"), "Samsung")
        self.assertEqual(canonical_brand_name("iphone"), "Apple")
        self.assertEqual(canonical_brand_name("cmf"), "CMF by Nothing")
        self.assertEqual(canonical_brand_name("unknown_new_brand"), "Unknown_New_Brand")

    def test_normalize_str(self):
        self.assertEqual(normalize_str("  Apple  iPhone 15  "), "apple iphone 15")
        self.assertEqual(normalize_str(None), "")
        self.assertEqual(normalize_str(123), "")

    def test_normalize_category(self):
        self.assertEqual(normalize_category("Home Appliances"), "home_appliances")
        self.assertEqual(normalize_category("appliances"), "home_appliances")
        self.assertEqual(normalize_category("Smartphones"), "mobiles")
        self.assertEqual(normalize_category("laptops"), "laptops")
        self.assertEqual(normalize_category("all"), "all")


if __name__ == "__main__":
    unittest.main()
