"""
Asaxiy.uz marketplace provider.
"""
from __future__ import annotations

from typing import Optional
from bs4 import BeautifulSoup

from providers.base import BaseProvider, ProductResult
from utils.http_client import fetch_html, fetch_json
from core.logging_config import get_logger

logger = get_logger(__name__)


class AsaxiyProvider(BaseProvider):
    name = "asaxiy"
    display_name = "Asaxiy"
    base_url = "https://asaxiy.uz"
    is_uzbek = True

    SEARCH_API = "https://asaxiy.uz/product"

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        results = []
        try:
            params = {"keyword": query, "limit": min(max_results, 20)}
            html = await fetch_html(self.SEARCH_API, params=params)
            if not html:
                return results

            soup = BeautifulSoup(html, "html.parser")

            # Try JSON-LD first
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    import json
                    data = json.loads(script.string or "")
                    if isinstance(data, dict) and data.get("@type") == "ItemList":
                        for item in data.get("itemListElement", []):
                            offer = item.get("item") or {}
                            price = None
                            if offer.get("offers"):
                                price = float(offer["offers"].get("price", 0)) or None
                            results.append(ProductResult(
                                title=offer.get("name", ""),
                                price=price,
                                currency="UZS",
                                availability=True,
                                rating=offer.get("aggregateRating", {}).get("ratingValue"),
                                review_count=int(offer.get("aggregateRating", {}).get("reviewCount", 0)),
                                image_url=offer.get("image"),
                                product_url=offer.get("url", self.base_url),
                                store=self.display_name,
                            ))
                except Exception:
                    pass

            if results:
                return results[:max_results]

            # Fallback: parse product cards
            cards = soup.select(".product-item, .product-card, [class*='product']")
            for card in cards[:max_results]:
                try:
                    title_el = card.select_one("h2, h3, .product-name, .title, [class*='name']")
                    price_el = card.select_one(".price, [class*='price'], .product-price")
                    img_el = card.select_one("img")
                    link_el = card.select_one("a")

                    title = title_el.get_text(strip=True) if title_el else ""
                    if not title:
                        continue

                    price_text = price_el.get_text(strip=True) if price_el else ""
                    price = self._parse_price(price_text)

                    image_url = None
                    if img_el:
                        image_url = img_el.get("src") or img_el.get("data-src")
                        if image_url and not image_url.startswith("http"):
                            image_url = self.base_url + image_url

                    product_url = self.base_url
                    if link_el and link_el.get("href"):
                        href = link_el["href"]
                        product_url = href if href.startswith("http") else self.base_url + href

                    results.append(ProductResult(
                        title=title,
                        price=price,
                        currency="UZS",
                        availability=True,
                        rating=None,
                        review_count=0,
                        image_url=image_url,
                        product_url=product_url,
                        store=self.display_name,
                    ))
                except Exception as e:
                    logger.warning("asaxiy_card_parse_error", error=str(e))
                    continue

        except Exception as e:
            logger.error("asaxiy_search_error", query=query, error=str(e))

        return results

    async def get_product(self, url: str) -> Optional[ProductResult]:
        try:
            html = await fetch_html(url)
            if not html:
                return None
            soup = BeautifulSoup(html, "html.parser")

            title = ""
            for sel in ["h1", ".product-title", "[class*='title']"]:
                el = soup.select_one(sel)
                if el:
                    title = el.get_text(strip=True)
                    break

            price = None
            for sel in [".product-price", ".price", "[class*='price']"]:
                el = soup.select_one(sel)
                if el:
                    price = self._parse_price(el.get_text(strip=True))
                    break

            img = soup.select_one(".product-image img, .gallery img, [class*='gallery'] img")
            image_url = None
            if img:
                image_url = img.get("src") or img.get("data-src")

            return ProductResult(
                title=title or "Unknown",
                price=price,
                currency="UZS",
                availability=True,
                rating=None,
                review_count=0,
                image_url=image_url,
                product_url=url,
                store=self.display_name,
            )
        except Exception as e:
            logger.error("asaxiy_get_product_error", url=url, error=str(e))
            return None

    def _parse_price(self, text: str) -> Optional[float]:
        try:
            cleaned = "".join(c for c in text if c.isdigit() or c == ".")
            return float(cleaned) if cleaned else None
        except Exception:
            return None

    async def supports_url(self, url: str) -> bool:
        return "asaxiy.uz" in url
