"""
Global marketplace providers.
AliExpress, Amazon, eBay, Temu, Wildberries.
"""
from __future__ import annotations

import re
from typing import Optional
from bs4 import BeautifulSoup

from providers.base import BaseProvider, ProductResult
from utils.http_client import fetch_html, fetch_json
from core.logging_config import get_logger

logger = get_logger(__name__)


def _parse_price(text: str) -> Optional[float]:
    try:
        cleaned = re.sub(r"[^\d.]", "", text.strip())
        return float(cleaned) if cleaned else None
    except Exception:
        return None


def _abs_url(base: str, path: Optional[str]) -> str:
    if not path:
        return base
    return path if path.startswith("http") else base + path


# ─────────────────────────────────────────────
# AliExpress
# ─────────────────────────────────────────────

class AliExpressProvider(BaseProvider):
    name = "aliexpress"
    display_name = "AliExpress"
    base_url = "https://www.aliexpress.com"
    is_uzbek = False

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        results = []
        try:
            # AliExpress has a public search endpoint that returns JSON
            params = {
                "SearchText": query,
                "catId": 0,
                "initiative_id": "SB_20241001",
                "page": 1,
                "g": "y",
            }
            # Use the open search page with JSON rendering hint
            data = await fetch_json(
                "https://www.aliexpress.com/wholesale",
                params={**params, "_fm": "search", "trafficChannel": "main"},
                headers={"Referer": "https://www.aliexpress.com"},
            )

            # If API fails, scrape HTML
            if not data or not isinstance(data, dict):
                return await self._html_search(query, max_results)

            items = (
                data.get("data", {}).get("root", {}).get("fields", {}).get("mods", {}).get("itemList", {}).get("content", [])
                or []
            )
            for item in items[:max_results]:
                try:
                    price_info = item.get("prices") or {}
                    price = None
                    if price_info:
                        sale = price_info.get("salePrice") or price_info.get("originalPrice") or {}
                        price = float(sale.get("minAmount", {}).get("value") or 0) or None

                    product_id = item.get("productId") or ""
                    url = f"https://www.aliexpress.com/item/{product_id}.html" if product_id else self.base_url

                    image_url = item.get("image") or item.get("imageUrl")
                    if image_url and image_url.startswith("//"):
                        image_url = "https:" + image_url

                    results.append(ProductResult(
                        title=item.get("title") or item.get("name") or "",
                        price=price, currency="USD",
                        availability=True,
                        rating=float(item.get("starRating") or 0) or None,
                        review_count=int(item.get("tradeDesc") or "").replace(",", "") if item.get("tradeDesc", "").replace(",", "").isdigit() else 0,
                        image_url=image_url,
                        product_url=url,
                        store=self.display_name,
                        external_id=str(product_id),
                    ))
                except Exception:
                    continue
        except Exception as e:
            logger.error("aliexpress_search_error", error=str(e))
            results = await self._html_search(query, max_results)

        return results

    async def _html_search(self, query: str, max_results: int) -> list[ProductResult]:
        results = []
        try:
            html = await fetch_html(
                "https://www.aliexpress.com/wholesale",
                params={"SearchText": query},
                headers={"Accept-Language": "en-US,en;q=0.9"},
            )
            if not html:
                return results
            soup = BeautifulSoup(html, "html.parser")

            # Look for JSON embedded in script
            for script in soup.find_all("script"):
                text = script.string or ""
                if "window._dida_config_" in text or "listItems" in text:
                    match = re.search(r'"listItems"\s*:\s*(\[.+?\])\s*,\s*"', text, re.DOTALL)
                    if match:
                        try:
                            import json
                            items = json.loads(match.group(1))
                            for item in items[:max_results]:
                                price = float(item.get("priceStr", "0").replace("$", "").replace(",", "") or 0) or None
                                results.append(ProductResult(
                                    title=item.get("title", ""),
                                    price=price, currency="USD", availability=True,
                                    rating=float(item.get("starRating") or 0) or None,
                                    review_count=0,
                                    image_url=("https:" + item["imgUrl"]) if item.get("imgUrl", "").startswith("//") else item.get("imgUrl"),
                                    product_url=("https:" + item["productDetailUrl"]) if item.get("productDetailUrl", "").startswith("//") else item.get("productDetailUrl", self.base_url),
                                    store=self.display_name,
                                ))
                        except Exception:
                            pass
                        break

            if not results:
                # Generic card parsing
                for card in soup.select(".item, [class*='product-item'], [class*='card']")[:max_results]:
                    title_el = card.select_one("h1, h3, [class*='title'], [class*='name']")
                    price_el = card.select_one("[class*='price']")
                    img_el = card.select_one("img")
                    link_el = card.select_one("a")
                    title = title_el.get_text(strip=True) if title_el else ""
                    if not title:
                        continue
                    href = link_el.get("href") if link_el else ""
                    if href and href.startswith("//"):
                        href = "https:" + href
                    results.append(ProductResult(
                        title=title,
                        price=_parse_price(price_el.get_text(strip=True) if price_el else ""),
                        currency="USD", availability=True, rating=None, review_count=0,
                        image_url=img_el.get("src") if img_el else None,
                        product_url=href or self.base_url, store=self.display_name,
                    ))
        except Exception as e:
            logger.error("aliexpress_html_error", error=str(e))
        return results

    async def get_product(self, url: str) -> Optional[ProductResult]:
        html = await fetch_html(url)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("h1.product-title-text, [class*='product-title'], h1")
        price = soup.select_one(".product-price-current, [class*='price-current'], [class*='uniform-banner-box-price']")
        img = soup.select_one(".magnifier-image, .images-view-item img, [class*='product-image'] img")
        return ProductResult(
            title=title.get_text(strip=True) if title else "Unknown",
            price=_parse_price(price.get_text(strip=True) if price else ""),
            currency="USD", availability=True, rating=None, review_count=0,
            image_url=img.get("src") if img else None,
            product_url=url, store=self.display_name,
        )

    async def supports_url(self, url: str) -> bool:
        return "aliexpress.com" in url


# ─────────────────────────────────────────────
# Amazon
# ─────────────────────────────────────────────

class AmazonProvider(BaseProvider):
    name = "amazon"
    display_name = "Amazon"
    base_url = "https://www.amazon.com"
    is_uzbek = False

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        results = []
        try:
            html = await fetch_html(
                f"{self.base_url}/s",
                params={"k": query},
                headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            if not html:
                return results
            soup = BeautifulSoup(html, "html.parser")

            cards = soup.select("[data-component-type='s-search-result']")
            for card in cards[:max_results]:
                try:
                    title_el = card.select_one("h2 .a-text-normal, h2 span")
                    price_whole = card.select_one(".a-price-whole")
                    price_frac = card.select_one(".a-price-fraction")
                    img_el = card.select_one("img.s-image, .s-product-image-container img")
                    link_el = card.select_one("h2 a, .a-link-normal")
                    rating_el = card.select_one(".a-icon-star-small .a-icon-alt, [class*='a-star'] .a-icon-alt")

                    title = title_el.get_text(strip=True) if title_el else ""
                    if not title:
                        continue

                    price = None
                    if price_whole:
                        price_str = price_whole.get_text(strip=True).replace(",", "")
                        frac = price_frac.get_text(strip=True) if price_frac else "00"
                        try:
                            price = float(f"{price_str}.{frac}")
                        except Exception:
                            price = _parse_price(price_str)

                    rating = None
                    if rating_el:
                        rating_text = rating_el.get_text(strip=True)
                        m = re.search(r"[\d.]+", rating_text)
                        if m:
                            rating = float(m.group())

                    href = link_el.get("href") if link_el else ""
                    url = _abs_url(self.base_url, href)

                    results.append(ProductResult(
                        title=title, price=price, currency="USD", availability=True,
                        rating=rating, review_count=0,
                        image_url=img_el.get("src") if img_el else None,
                        product_url=url, store=self.display_name,
                    ))
                except Exception:
                    continue
        except Exception as e:
            logger.error("amazon_search_error", error=str(e))
        return results

    async def get_product(self, url: str) -> Optional[ProductResult]:
        html = await fetch_html(url, headers={"Accept-Language": "en-US,en;q=0.9"})
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("#productTitle, h1.a-size-large")
        price = soup.select_one(".a-price-whole, #priceblock_ourprice, .a-offscreen")
        img = soup.select_one("#imgTagWrapperId img, #landingImage")
        return ProductResult(
            title=title.get_text(strip=True) if title else "Unknown",
            price=_parse_price(price.get_text(strip=True) if price else ""),
            currency="USD", availability=True, rating=None, review_count=0,
            image_url=img.get("src") if img else None,
            product_url=url, store=self.display_name,
        )

    async def supports_url(self, url: str) -> bool:
        return "amazon.com" in url or "amazon.co" in url


# ─────────────────────────────────────────────
# eBay
# ─────────────────────────────────────────────

class EbayProvider(BaseProvider):
    name = "ebay"
    display_name = "eBay"
    base_url = "https://www.ebay.com"
    is_uzbek = False

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        results = []
        try:
            html = await fetch_html(
                f"{self.base_url}/sch/i.html",
                params={"_nkw": query, "_ipg": min(max_results, 25)},
            )
            if not html:
                return results
            soup = BeautifulSoup(html, "html.parser")
            for card in soup.select(".s-item")[:max_results + 2]:
                try:
                    title_el = card.select_one(".s-item__title")
                    price_el = card.select_one(".s-item__price")
                    img_el = card.select_one(".s-item__image-img")
                    link_el = card.select_one(".s-item__link")

                    title = title_el.get_text(strip=True) if title_el else ""
                    if not title or title.lower() == "shop on ebay":
                        continue

                    results.append(ProductResult(
                        title=title,
                        price=_parse_price(price_el.get_text(strip=True) if price_el else ""),
                        currency="USD", availability=True, rating=None, review_count=0,
                        image_url=img_el.get("src") if img_el else None,
                        product_url=link_el.get("href") if link_el else self.base_url,
                        store=self.display_name,
                    ))
                except Exception:
                    continue
        except Exception as e:
            logger.error("ebay_search_error", error=str(e))
        return results[:max_results]

    async def get_product(self, url: str) -> Optional[ProductResult]:
        html = await fetch_html(url)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("h1.x-item-title__mainTitle span, h1")
        price = soup.select_one(".x-price-primary span, .notranslate")
        img = soup.select_one("#icImg, .ux-image-carousel-item img")
        return ProductResult(
            title=title.get_text(strip=True) if title else "Unknown",
            price=_parse_price(price.get_text(strip=True) if price else ""),
            currency="USD", availability=True, rating=None, review_count=0,
            image_url=img.get("src") if img else None,
            product_url=url, store=self.display_name,
        )

    async def supports_url(self, url: str) -> bool:
        return "ebay.com" in url


# ─────────────────────────────────────────────
# Temu
# ─────────────────────────────────────────────

class TemuProvider(BaseProvider):
    name = "temu"
    display_name = "Temu"
    base_url = "https://www.temu.com"
    is_uzbek = False

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        results = []
        try:
            html = await fetch_html(
                f"{self.base_url}/search_result.html",
                params={"search_key": query, "search_method": "user"},
                headers={"Accept-Language": "en-US,en;q=0.9"},
            )
            if not html:
                return results
            soup = BeautifulSoup(html, "html.parser")
            for card in soup.select("[class*='product-card'], [class*='goods-item'], [data-goods-id]")[:max_results]:
                title_el = card.select_one("[class*='title'], [class*='name']")
                price_el = card.select_one("[class*='price']")
                img_el = card.select_one("img")
                link_el = card.select_one("a")
                title = title_el.get_text(strip=True) if title_el else ""
                if not title:
                    continue
                href = link_el.get("href") if link_el else ""
                results.append(ProductResult(
                    title=title,
                    price=_parse_price(price_el.get_text(strip=True) if price_el else ""),
                    currency="USD", availability=True, rating=None, review_count=0,
                    image_url=img_el.get("src") if img_el else None,
                    product_url=_abs_url(self.base_url, href),
                    store=self.display_name,
                ))
        except Exception as e:
            logger.error("temu_search_error", error=str(e))
        return results

    async def get_product(self, url: str) -> Optional[ProductResult]:
        html = await fetch_html(url)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("h1, [class*='product-title']")
        price = soup.select_one("[class*='price']")
        img = soup.select_one("[class*='product-image'] img, [class*='gallery'] img")
        return ProductResult(
            title=title.get_text(strip=True) if title else "Unknown",
            price=_parse_price(price.get_text(strip=True) if price else ""),
            currency="USD", availability=True, rating=None, review_count=0,
            image_url=img.get("src") if img else None,
            product_url=url, store=self.display_name,
        )

    async def supports_url(self, url: str) -> bool:
        return "temu.com" in url


# ─────────────────────────────────────────────
# Wildberries
# ─────────────────────────────────────────────

class WildberriesProvider(BaseProvider):
    name = "wildberries"
    display_name = "Wildberries"
    base_url = "https://www.wildberries.ru"
    is_uzbek = False

    SEARCH_API = "https://search.wb.ru/exactmatch/ru/common/v4/search"

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        results = []
        try:
            params = {
                "appType": 1,
                "curr": "rub",
                "dest": -1257786,
                "query": query,
                "resultset": "catalog",
                "sort": "popular",
                "spp": 27,
                "suppressSpellcheck": False,
            }
            data = await fetch_json(self.SEARCH_API, params=params)
            if not data:
                return results

            products = data.get("data", {}).get("products") or []
            for p in products[:max_results]:
                try:
                    price = float(p.get("salePriceU") or p.get("priceU") or 0) / 100 or None
                    nm_id = p.get("id")
                    image_url = f"https://basket-01.wb.ru/vol{nm_id // 100000}/part{nm_id // 1000}/{nm_id}/images/big/1.jpg" if nm_id else None
                    url = f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx" if nm_id else self.base_url

                    results.append(ProductResult(
                        title=p.get("name") or "",
                        price=price, currency="RUB", availability=True,
                        rating=float(p.get("rating") or 0) or None,
                        review_count=int(p.get("feedbacks") or 0),
                        image_url=image_url,
                        product_url=url,
                        store=self.display_name,
                        external_id=str(nm_id),
                        brand=p.get("brand"),
                    ))
                except Exception:
                    continue
        except Exception as e:
            logger.error("wildberries_search_error", error=str(e))
        return results

    async def get_product(self, url: str) -> Optional[ProductResult]:
        try:
            m = re.search(r"/catalog/(\d+)/", url)
            if not m:
                return None
            nm_id = int(m.group(1))
            data = await fetch_json(
                f"https://card.wb.ru/cards/detail",
                params={"nm": nm_id, "curr": "rub", "dest": -1257786, "spp": 27},
            )
            if not data:
                return None
            p = (data.get("data", {}).get("products") or [{}])[0]
            price = float(p.get("salePriceU") or p.get("priceU") or 0) / 100 or None
            image_url = f"https://basket-01.wb.ru/vol{nm_id // 100000}/part{nm_id // 1000}/{nm_id}/images/big/1.jpg"
            return ProductResult(
                title=p.get("name") or "Unknown",
                price=price, currency="RUB", availability=True,
                rating=float(p.get("rating") or 0) or None,
                review_count=int(p.get("feedbacks") or 0),
                image_url=image_url,
                product_url=url, store=self.display_name,
                external_id=str(nm_id),
                brand=p.get("brand"),
            )
        except Exception as e:
            logger.error("wildberries_get_product_error", url=url, error=str(e))
            return None

    async def supports_url(self, url: str) -> bool:
        return "wildberries.ru" in url or "wb.ru" in url
