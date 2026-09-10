"""
tests/test_analytics.py — Unit tests for Holt-Winters forecasting, MAPE accuracy, and search queries.
"""
import unittest
import pandas as pd
import datetime

from core.analytics import (
    compute_holt_winters_forecast,
    compute_forecast_accuracy_mape,
    get_best_time_to_buy_recommendation,
    product_matches_query,
)


class TestAnalytics(unittest.TestCase):
    def setUp(self):
        dates = [datetime.date.today() - datetime.timedelta(days=i) for i in range(20, -1, -1)]
        prices = [50000.0 - i * 150.0 for i in range(21)]
        self.series = pd.Series(prices, index=dates)

    def test_holt_winters_forecast_structure(self):
        fc = compute_holt_winters_forecast(self.series, horizon_days=7)
        self.assertIn("current_price", fc)
        self.assertIn("predicted_7d", fc)
        self.assertIn("trend", fc)
        self.assertIn("confidence", fc)
        self.assertEqual(len(fc["future_dates"]), 7)
        self.assertEqual(len(fc["forecast_series"]), 7)
        self.assertIn(fc["confidence"], ["HIGH", "MED", "LOW"])

    def test_forecast_accuracy_mape(self):
        mape = compute_forecast_accuracy_mape(self.series)
        self.assertIsNotNone(mape)
        self.assertGreaterEqual(mape, 0.0)

    def test_best_time_to_buy_recommendation(self):
        # Current price near low
        rec_buy = get_best_time_to_buy_recommendation(
            current_price=47000.0, price_history=self.series, forecast_trend="down"
        )
        self.assertIn("verdict", rec_buy)
        self.assertIn("explanation", rec_buy)

    def test_product_matches_query(self):
        self.assertTrue(
            product_matches_query(
                p_name="Apple iPhone 15 Pro Max 256GB Blue",
                brand_raw="Apple",
                brand_norm="apple",
                category="mobiles",
                query="iphone 15 pro",
            )
        )
        # Synonym expansion: "phone" should match "Apple iPhone"
        self.assertTrue(
            product_matches_query(
                p_name="Apple iPhone 15",
                brand_raw="Apple",
                brand_norm="apple",
                category="mobiles",
                query="apple phone",
            )
        )
        # Unit normalization: "256 gb" should match "256GB"
        self.assertTrue(
            product_matches_query(
                p_name="Apple iPhone 15 256GB",
                brand_raw="Apple",
                brand_norm="apple",
                category="mobiles",
                query="256 gb",
            )
        )
        # Unrelated query should not match
        self.assertFalse(
            product_matches_query(
                p_name="Samsung Galaxy S24",
                brand_raw="Samsung",
                brand_norm="samsung",
                category="mobiles",
                query="macbook",
            )
        )


if __name__ == "__main__":
    unittest.main()
