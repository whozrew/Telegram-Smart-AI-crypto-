"""
OLX Uzbekistan provider.
Uses OLX UZ public API / web scraping.
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import urlencode, quote

from providers.base import BaseProvider, ProductResult
from utils.http_client import fetch_html, fetch_json
from core.logging_config import get_logger

logger = get_logger(__name__)

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class OlxProvider(BaseProvider):
    name = "olx"
    display_name = "OLX Uzbekistan"
    base_url = "https://www.olx.uz"
    is_uzbek = True

    SEARCH_URL = "https://www.olx.uz/api/v1/offers/"

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        results = []
        try:
            # Try OLX API
            params = {
                "query": query,
                "limit": min(max_results, 40),
                "offset": 0,
                "sort_by": "relevance:desc",
            }
            headers = {
                "x-olx-app-version": "1.0.0",
            }
            data = await fetch_json(self.SEARCH_URL, params=params, headers=headers)

            if data and isinstance(data, dict) and data.get("data"):
                for item in data["data"][:max_results]:
                    try:
                        price_obj = item.get("price") or {}
                        price = None
                        currency = "UZS"
                        if price_obj:
                            price = float(price_obj.get("value", {}).get("raw", 0) or 0) or None
                            currency = price_obj.get("currency", "UZS")

                        photos = item.get("photos") or []
                        image_url = None
                        if photos:
                            image_url = photos[0].get("link", "").replace("{width}", "400").replace("{height}", "400")

                        item_url = item.get("url") or self.base_url

                        results.append(ProductResult(
                            title=item.get("title", ""),
                            price=price,
                            currency=currency,
                            availability=True,
                            rating=None,
                            review_count=0,
                            image_url=image_url,
                            product_url=item_url,
                            store=self.display_name,
                            external_id=str(item.get("id", "")),
                            description=item.get("description", ""),
                        ))
                    except Exception as e:
                        logger.warning("olx_item_parse_error", error=str(e))
                        continue
            else:
                # Fallback: HTML scraping
                results = await self._scrape_html(query, max_results)

        except Exception as e:
            logger.error("olx_search_error", query=query, error=str(e))

        return results

    async def _scrape_html(self, query: str, max_results: int) -> list[ProductResult]:
        results = []
        if not BS4_AVAILABLE:
            return results
        try:
            url = f"{self.base_url}/uzbekistan/q-{quote(query.replace(' ', '-'))}/"
            html = await fetch_html(url)
            if not html:
                return results

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("[data-cy='l-card'], .offer-wrapper, [class*='offer']")

            for card in cards[:max_results]:
                try:
                    title_el = card.select_one("h6, h3, [class*='title']")
                    price_el = card.select_one("[data-testid='ad-price'], [class*='price']")
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
                except Exception:
                    continue
        except Exception as e:
            logger.error("olx_html_scrape_error", query=query, error=str(e))

        return results

    def _parse_price(self, text: str) -> Optional[float]:
        try:
            cleaned = "".join(c for c in text if c.isdigit())
            return float(cleaned) if cleaned else None
        except Exception:
            return None

    async def get_product(self, url: str) -> Optional[ProductResult]:
        if not BS4_AVAILABLE:
            return None
        try:
            html = await fetch_html(url)
            if not html:
                return None
            soup = BeautifulSoup(html, "html.parser")

            title_el = soup.select_one("h1, [data-cy='ad_title']")
            price_el = soup.select_one("[data-testid='ad-price-container'], .price-label")
            img_el = soup.select_one(".photo-item img, [class*='photo'] img")

            title = title_el.get_text(strip=True) if title_el else "Unknown"
            price = self._parse_price(price_el.get_text(strip=True) if price_el else "")
            image_url = img_el.get("src") if img_el else None

            return ProductResult(
                title=title,
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
            logger.error("olx_get_product_error", url=url, error=str(e))
            return None

    async def supports_url(self, url: str) -> bool:
        return "olx.uz" in url
