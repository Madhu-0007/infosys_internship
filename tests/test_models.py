"""
tests/test_models.py — Unit tests for ProductItem and CompetitorPair domain models.
"""
import unittest
import pandas as pd

from core.models import ProductItem, CompetitorPair


class TestProductItem(unittest.TestCase):
    def test_from_series(self):
        s = pd.Series({
            "product_name": "Apple iPhone 15 Pro",
            "price": 129990.0,
            "mrp": 139990.0,
            "discount": 7.0,
            "rating": 4.7,
            "url": "https://www.flipkart.com/apple-iphone-15-pro",
            "source": "flipkart",
            "category": "mobiles",
            "matched_id": "MATCH_001",
        })
        item = ProductItem.from_series(s)
        self.assertEqual(item.product_name, "Apple iPhone 15 Pro")
        self.assertEqual(item.price, 129990.0)
        self.assertEqual(item.rating, 4.7)
        self.assertEqual(item.source, "flipkart")
        self.assertEqual(item.matched_id, "MATCH_001")


class TestCompetitorPair(unittest.TestCase):
    def setUp(self):
        self.fk_item = ProductItem(
            product_name="Samsung Galaxy S24 Ultra",
            price=119999.0,
            mrp=129999.0,
            discount=8.0,
            source="flipkart",
            category="mobiles",
        )
        self.az_item_cheaper = ProductItem(
            product_name="Samsung Galaxy S24 Ultra",
            price=114999.0,
            mrp=129999.0,
            discount=12.0,
            source="amazon",
            category="mobiles",
        )
        self.az_item_costlier = ProductItem(
            product_name="Samsung Galaxy S24 Ultra",
            price=124999.0,
            mrp=129999.0,
            discount=4.0,
            source="amazon",
            category="mobiles",
        )

    def test_amazon_cheaper_advantage(self):
        pair = CompetitorPair(fk=self.fk_item, az=self.az_item_cheaper)
        self.assertTrue(pair.has_amazon)
        self.assertEqual(pair.price_diff, 5000.0)
        self.assertEqual(pair.abs_diff, 5000.0)
        self.assertEqual(pair.cheaper_store, "Amazon")
        self.assertIn("Amazon leads by ₹5,000", pair.edge_text)

    def test_flipkart_cheaper_advantage(self):
        pair = CompetitorPair(fk=self.fk_item, az=self.az_item_costlier)
        self.assertTrue(pair.has_amazon)
        self.assertEqual(pair.price_diff, -5000.0)
        self.assertEqual(pair.abs_diff, 5000.0)
        self.assertEqual(pair.cheaper_store, "Flipkart")
        self.assertIn("Flipkart leads by ₹5,000", pair.edge_text)

    def test_exact_price_parity(self):
        az_parity = ProductItem(
            product_name="Samsung Galaxy S24 Ultra",
            price=119999.0,
            source="amazon",
        )
        pair = CompetitorPair(fk=self.fk_item, az=az_parity)
        self.assertEqual(pair.price_diff, 0.0)
        self.assertEqual(pair.cheaper_store, "Tie")
        self.assertEqual(pair.edge_text, "Exact price parity across platforms.")

    def test_solo_flipkart_listing(self):
        pair = CompetitorPair(fk=self.fk_item, az=None)
        self.assertFalse(pair.has_amazon)
        self.assertEqual(pair.price_diff, 0.0)
        self.assertEqual(pair.cheaper_store, "Solo")
        self.assertIn("Exclusive listing on Flipkart", pair.edge_text)


if __name__ == "__main__":
    unittest.main()
