"""
Base provider interface.
All marketplace providers must implement this.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ProductResult:
    title: str
    price: Optional[float]
    currency: str
    availability: bool
    rating: Optional[float]
    review_count: int
    image_url: Optional[str]
    product_url: str
    store: str
    store_logo: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    specifications: dict = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    external_id: Optional[str] = None
    description: Optional[str] = None

    def price_display(self) -> str:
        if self.price is None:
            return "N/A"
        if self.currency == "UZS":
            return f"{self.price:,.0f} so'm"
        elif self.currency == "USD":
            return f"${self.price:,.2f}"
        elif self.currency == "RUB":
            return f"₽{self.price:,.0f}"
        return f"{self.price:,.2f} {self.currency}"

    def rating_display(self) -> str:
        if self.rating is None:
            return "N/A"
        return f"{'⭐' * round(self.rating)} ({self.rating:.1f})"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "price": self.price,
            "currency": self.currency,
            "availability": self.availability,
            "rating": self.rating,
            "review_count": self.review_count,
            "image_url": self.image_url,
            "product_url": self.product_url,
            "store": self.store,
            "store_logo": self.store_logo,
            "category": self.category,
            "brand": self.brand,
            "specifications": self.specifications,
            "last_updated": self.last_updated.isoformat(),
            "external_id": self.external_id,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProductResult":
        d = d.copy()
        if isinstance(d.get("last_updated"), str):
            try:
                d["last_updated"] = datetime.fromisoformat(d["last_updated"])
            except Exception:
                d["last_updated"] = datetime.utcnow()
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class BaseProvider(abc.ABC):
    """Abstract base class for all marketplace providers."""

    name: str = "base"
    display_name: str = "Base Store"
    base_url: str = ""
    logo_url: Optional[str] = None
    is_uzbek: bool = True

    @abc.abstractmethod
    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        """Search for products by query string."""
        ...

    @abc.abstractmethod
    async def get_product(self, url: str) -> Optional[ProductResult]:
        """Fetch a single product by its URL."""
        ...

    async def supports_url(self, url: str) -> bool:
        """Return True if this provider handles the given URL."""
        return self.base_url in url

    def __repr__(self) -> str:
        return f"<Provider: {self.name}>"
