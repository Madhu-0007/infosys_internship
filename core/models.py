"""
core/models.py — Strongly typed domain dataclasses for the Competitor Intelligence Engine.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Any
import pandas as pd


@dataclass
class ProductItem:
    """Represents a single scraped or indexed product listing on a retail platform."""
    product_name: str
    price: float
    mrp: float = 0.0
    discount: float = 0.0
    rating: float = 4.0
    url: str = ""
    source: str = "flipkart"
    category: str = "all"
    matched_id: Optional[str] = None
    scraped_at: Optional[str] = None

    @classmethod
    def from_series(cls, s: pd.Series, default_category: str = "all") -> "ProductItem":
        """Construct a ProductItem from a pandas Series row."""
        return cls(
            product_name=str(s.get("product_name", "Unknown Product")),
            price=float(s.get("price", 0.0) or 0.0),
            mrp=float(s.get("mrp", 0.0) or 0.0),
            discount=float(s.get("discount", 0.0) or 0.0),
            rating=float(s.get("rating", 4.0) or 4.0),
            url=str(s.get("url", "")).strip(),
            source=str(s.get("source", "flipkart")).strip().lower(),
            category=str(s.get("category", default_category)).strip(),
            matched_id=str(s.get("matched_id", "")) if pd.notna(s.get("matched_id")) else None,
            scraped_at=str(s.get("scraped_at", "")) if pd.notna(s.get("scraped_at")) else None,
        )


@dataclass
class CompetitorPair:
    """Represents a paired Flipkart vs Amazon competitor product comparison."""
    fk: ProductItem
    az: Optional[ProductItem] = None

    @property
    def has_amazon(self) -> bool:
        return self.az is not None and self.az.price > 0

    @property
    def price_diff(self) -> float:
        """Positive means Flipkart is more expensive (Amazon is cheaper)."""
        if not self.has_amazon:
            return 0.0
        return self.fk.price - self.az.price

    @property
    def abs_diff(self) -> float:
        return abs(self.price_diff)

    @property
    def pct_diff(self) -> float:
        if not self.has_amazon:
            return 0.0
        higher = max(self.fk.price, self.az.price)
        return (self.abs_diff / higher * 100.0) if higher > 0 else 0.0

    @property
    def cheaper_store(self) -> str:
        if not self.has_amazon:
            return "Solo"
        if self.price_diff > 0:
            return "Amazon"
        elif self.price_diff < 0:
            return "Flipkart"
        return "Tie"

    @property
    def edge_text(self) -> str:
        if not self.has_amazon:
            return "Exclusive listing on Flipkart. No direct Amazon match found."
        if self.price_diff > 0:
            return f"Amazon leads by ₹{self.abs_diff:,.0f} ({self.pct_diff:.1f}% cheaper). Superior value."
        elif self.price_diff < 0:
            return f"Flipkart leads by ₹{self.abs_diff:,.0f} ({self.pct_diff:.1f}% cheaper). Better price."
        return "Exact price parity across platforms."


@dataclass
class ForecastResult:
    """Holds 7-day Holt-Winters price forecasting results and confidence envelopes."""
    current_price: float
    predicted_7d: float
    trend: str  # "up", "down", "flat"
    confidence: str  # "HIGH", "MED", "LOW"
    future_dates: List[Any]
    forecast_series: pd.Series
    upper_band: pd.Series
    lower_band: pd.Series
    mape: Optional[float] = None


@dataclass
class SentimentSummary:
    """Aggregated sentiment analysis distribution and authentic review quotes."""
    positive: int
    neutral: int
    negative: int
    overall_score: float
    fk_snippets: List[str] = field(default_factory=list)
    az_snippets: List[str] = field(default_factory=list)
