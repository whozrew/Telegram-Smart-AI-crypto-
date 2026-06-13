"""
Uzbek store providers: MediaPark, Texnomart, Idea, Goodzone, ZoodMall.
All use similar HTML scraping with BeautifulSoup.
"""
from __future__ import annotations

import json
import re
from typing import Optional
from bs4 import BeautifulSoup

from providers.base import BaseProvider, ProductResult
from utils.http_client import fetch_html, fetch_json
from core.logging_config import get_logger

logger = get_logger(__name__)


def _parse_price(text: str) -> Optional[float]:
    try:
        cleaned = re.sub(r"[^\d.]", "", text.replace(",", "").replace(" ", ""))
        return float(cleaned) if cleaned else None
    except Exception:
        return None


def _abs_url(base: str, path: str) -> str:
    if not path:
        return base
    return path if path.startswith("http") else base.rstrip("/") + "/" + path.lstrip("/")


# ─────────────────────────────────────────────
# MediaPark
# ─────────────────────────────────────────────

class MediaParkProvider(BaseProvider):
    name = "mediapark"
    display_name = "MediaPark"
    base_url = "https://mediapark.uz"
    is_uzbek = True

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        results = []
        try:
            api_url = f"{self.base_url}/api/catalog/search"
            data = await fetch_json(api_url, params={"q": query, "limit": max_results})
            if data:
                items = data.get("items") or data.get("products") or data.get("data") or []
                for item in items[:max_results]:
                    results.append(self._parse_api_item(item))
            if not results:
                results = await self._html_search(query, max_results)
        except Exception as e:
            logger.error("mediapark_search_error", error=str(e))
        return [r for r in results if r is not None]

    def _parse_api_item(self, item: dict) -> Optional[ProductResult]:
        try:
            price = float(item.get("price") or item.get("currentPrice") or 0) or None
            image_url = item.get("image") or item.get("photo") or item.get("thumbnail")
            if image_url and not image_url.startswith("http"):
                image_url = _abs_url(self.base_url, image_url)
            url = item.get("url") or item.get("link") or self.base_url
            if not url.startswith("http"):
                url = _abs_url(self.base_url, url)
            return ProductResult(
                title=item.get("name") or item.get("title") or "Unknown",
                price=price, currency="UZS",
                availability=item.get("inStock", True),
                rating=item.get("rating"),
                review_count=int(item.get("reviewCount") or 0),
                image_url=image_url, product_url=url,
                store=self.display_name,
                external_id=str(item.get("id") or ""),
            )
        except Exception:
            return None

    async def _html_search(self, query: str, max_results: int) -> list[ProductResult]:
        results = []
        html = await fetch_html(f"{self.base_url}/search", params={"q": query})
        if not html:
            return results
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select(".product-card, .catalog-item, [class*='product-item']")[:max_results]:
            title_el = card.select_one("h2, h3, .name, [class*='name'], [class*='title']")
            price_el = card.select_one(".price, [class*='price']")
            img_el = card.select_one("img")
            link_el = card.select_one("a")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue
            image_url = None
            if img_el:
                src = img_el.get("src") or img_el.get("data-src")
                image_url = _abs_url(self.base_url, src) if src else None
            href = link_el.get("href") if link_el else None
            url = _abs_url(self.base_url, href) if href else self.base_url
            results.append(ProductResult(
                title=title, price=_parse_price(price_el.get_text(strip=True) if price_el else ""),
                currency="UZS", availability=True, rating=None, review_count=0,
                image_url=image_url, product_url=url, store=self.display_name,
            ))
        return results

    async def get_product(self, url: str) -> Optional[ProductResult]:
        html = await fetch_html(url)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        title = (soup.select_one("h1") or soup.select_one("[class*='title']"))
        price = soup.select_one(".price, [class*='price']")
        img = soup.select_one(".product-gallery img, [class*='gallery'] img, .product-image img")
        return ProductResult(
            title=title.get_text(strip=True) if title else "Unknown",
            price=_parse_price(price.get_text(strip=True) if price else ""),
            currency="UZS", availability=True, rating=None, review_count=0,
            image_url=img.get("src") if img else None, product_url=url, store=self.display_name,
        )

    async def supports_url(self, url: str) -> bool:
        return "mediapark.uz" in url


# ─────────────────────────────────────────────
# Texnomart
# ─────────────────────────────────────────────

class TexnomartProvider(BaseProvider):
    name = "texnomart"
    display_name = "Texnomart"
    base_url = "https://texnomart.uz"
    is_uzbek = True

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        results = []
        try:
            html = await fetch_html(f"{self.base_url}/uz/search", params={"q": query})
            if not html:
                return results
            soup = BeautifulSoup(html, "html.parser")
            for card in soup.select(".product-item, .catalog-item, [class*='product-card']")[:max_results]:
                title_el = card.select_one(".product-name, h2, h3, [class*='name']")
                price_el = card.select_one(".product-price, .price, [class*='price']")
                img_el = card.select_one("img")
                link_el = card.select_one("a")
                title = title_el.get_text(strip=True) if title_el else ""
                if not title:
                    continue
                img_src = (img_el.get("src") or img_el.get("data-src")) if img_el else None
                href = link_el.get("href") if link_el else None
                results.append(ProductResult(
                    title=title,
                    price=_parse_price(price_el.get_text(strip=True) if price_el else ""),
                    currency="UZS", availability=True, rating=None, review_count=0,
                    image_url=_abs_url(self.base_url, img_src) if img_src else None,
                    product_url=_abs_url(self.base_url, href) if href else self.base_url,
                    store=self.display_name,
                ))
        except Exception as e:
            logger.error("texnomart_search_error", error=str(e))
        return results

    async def get_product(self, url: str) -> Optional[ProductResult]:
        html = await fetch_html(url)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("h1, .product-name")
        price = soup.select_one(".product-price, .price")
        img = soup.select_one(".product-gallery img, .product-photo img")
        return ProductResult(
            title=title.get_text(strip=True) if title else "Unknown",
            price=_parse_price(price.get_text(strip=True) if price else ""),
            currency="UZS", availability=True, rating=None, review_count=0,
            image_url=img.get("src") if img else None,
            product_url=url, store=self.display_name,
        )

    async def supports_url(self, url: str) -> bool:
        return "texnomart.uz" in url


# ─────────────────────────────────────────────
# Idea
# ─────────────────────────────────────────────

class IdeaProvider(BaseProvider):
    name = "idea"
    display_name = "Idea"
    base_url = "https://idea.uz"
    is_uzbek = True

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        results = []
        try:
            # Idea has a search endpoint
            data = await fetch_json(
                f"{self.base_url}/api/search",
                params={"term": query, "count": max_results}
            )
            if data:
                products = data.get("products") or data.get("items") or []
                for p in products[:max_results]:
                    price = float(p.get("price") or p.get("current_price") or 0) or None
                    url = p.get("url") or p.get("link") or self.base_url
                    results.append(ProductResult(
                        title=p.get("name") or p.get("title") or "",
                        price=price, currency="UZS", availability=p.get("available", True),
                        rating=p.get("rating"), review_count=int(p.get("reviews_count") or 0),
                        image_url=p.get("image") or p.get("photo"),
                        product_url=_abs_url(self.base_url, url),
                        store=self.display_name,
                    ))
            if not results:
                results = await self._html_search(query, max_results)
        except Exception as e:
            logger.error("idea_search_error", error=str(e))
        return results

    async def _html_search(self, query: str, max_results: int) -> list[ProductResult]:
        results = []
        html = await fetch_html(f"{self.base_url}/search", params={"q": query})
        if not html:
            return results
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select(".product, .catalog-product, [class*='product-item']")[:max_results]:
            title_el = card.select_one(".product__name, .product-name, h2, h3")
            price_el = card.select_one(".product__price, .price")
            img_el = card.select_one("img")
            link_el = card.select_one("a")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue
            results.append(ProductResult(
                title=title,
                price=_parse_price(price_el.get_text(strip=True) if price_el else ""),
                currency="UZS", availability=True, rating=None, review_count=0,
                image_url=_abs_url(self.base_url, img_el.get("src") or img_el.get("data-src")) if img_el else None,
                product_url=_abs_url(self.base_url, link_el.get("href")) if link_el else self.base_url,
                store=self.display_name,
            ))
        return results

    async def get_product(self, url: str) -> Optional[ProductResult]:
        html = await fetch_html(url)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("h1, .product__name")
        price = soup.select_one(".product__price, .price")
        img = soup.select_one(".product__image img, .product-image img")
        return ProductResult(
            title=title.get_text(strip=True) if title else "Unknown",
            price=_parse_price(price.get_text(strip=True) if price else ""),
            currency="UZS", availability=True, rating=None, review_count=0,
            image_url=img.get("src") if img else None,
            product_url=url, store=self.display_name,
        )

    async def supports_url(self, url: str) -> bool:
        return "idea.uz" in url


# ─────────────────────────────────────────────
# Goodzone
# ─────────────────────────────────────────────

class GoodzoneProvider(BaseProvider):
    name = "goodzone"
    display_name = "Goodzone"
    base_url = "https://goodzone.uz"
    is_uzbek = True

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        results = []
        try:
            html = await fetch_html(f"{self.base_url}/search", params={"q": query})
            if not html:
                return results
            soup = BeautifulSoup(html, "html.parser")
            for card in soup.select(".product-card, [class*='product-item'], .product")[:max_results]:
                title_el = card.select_one("h2, h3, .product-name, [class*='name']")
                price_el = card.select_one(".price, [class*='price']")
                img_el = card.select_one("img")
                link_el = card.select_one("a")
                title = title_el.get_text(strip=True) if title_el else ""
                if not title:
                    continue
                results.append(ProductResult(
                    title=title,
                    price=_parse_price(price_el.get_text(strip=True) if price_el else ""),
                    currency="UZS", availability=True, rating=None, review_count=0,
                    image_url=_abs_url(self.base_url, img_el.get("src") or img_el.get("data-src")) if img_el else None,
                    product_url=_abs_url(self.base_url, link_el.get("href")) if link_el else self.base_url,
                    store=self.display_name,
                ))
        except Exception as e:
            logger.error("goodzone_search_error", error=str(e))
        return results

    async def get_product(self, url: str) -> Optional[ProductResult]:
        html = await fetch_html(url)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("h1")
        price = soup.select_one(".price, [class*='price']")
        img = soup.select_one(".product-image img, [class*='gallery'] img")
        return ProductResult(
            title=title.get_text(strip=True) if title else "Unknown",
            price=_parse_price(price.get_text(strip=True) if price else ""),
            currency="UZS", availability=True, rating=None, review_count=0,
            image_url=img.get("src") if img else None,
            product_url=url, store=self.display_name,
        )

    async def supports_url(self, url: str) -> bool:
        return "goodzone.uz" in url


# ─────────────────────────────────────────────
# ZoodMall
# ─────────────────────────────────────────────

class ZoodmallProvider(BaseProvider):
    name = "zoodmall"
    display_name = "ZoodMall"
    base_url = "https://www.zoodmall.uz"
    is_uzbek = True

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        results = []
        try:
            data = await fetch_json(
                f"{self.base_url}/api/v1/search",
                params={"query": query, "limit": max_results, "page": 1}
            )
            if data:
                products = data.get("products") or data.get("data") or data.get("items") or []
                for p in products[:max_results]:
                    price = float(p.get("price") or p.get("sale_price") or 0) or None
                    image_url = p.get("image") or p.get("thumbnail")
                    results.append(ProductResult(
                        title=p.get("name") or p.get("title") or "",
                        price=price, currency="UZS",
                        availability=p.get("in_stock", True),
                        rating=float(p.get("rating") or 0) or None,
                        review_count=int(p.get("reviews") or 0),
                        image_url=image_url,
                        product_url=_abs_url(self.base_url, p.get("url") or p.get("slug") or ""),
                        store=self.display_name,
                    ))
            if not results:
                results = await self._html_search(query, max_results)
        except Exception as e:
            logger.error("zoodmall_search_error", error=str(e))
        return results

    async def _html_search(self, query: str, max_results: int) -> list[ProductResult]:
        results = []
        html = await fetch_html(f"{self.base_url}/search", params={"q": query})
        if not html:
            return results
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select(".product-card, .product-item, [class*='product']")[:max_results]:
            title_el = card.select_one("h2, h3, .name, [class*='title']")
            price_el = card.select_one(".price, [class*='price']")
            img_el = card.select_one("img")
            link_el = card.select_one("a")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue
            results.append(ProductResult(
                title=title,
                price=_parse_price(price_el.get_text(strip=True) if price_el else ""),
                currency="UZS", availability=True, rating=None, review_count=0,
                image_url=_abs_url(self.base_url, img_el.get("src") or img_el.get("data-src")) if img_el else None,
                product_url=_abs_url(self.base_url, link_el.get("href")) if link_el else self.base_url,
                store=self.display_name,
            ))
        return results

    async def get_product(self, url: str) -> Optional[ProductResult]:
        html = await fetch_html(url)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("h1, .product-title")
        price = soup.select_one(".price, [class*='price']")
        img = soup.select_one(".product-image img, [class*='gallery'] img")
        return ProductResult(
            title=title.get_text(strip=True) if title else "Unknown",
            price=_parse_price(price.get_text(strip=True) if price else ""),
            currency="UZS", availability=True, rating=None, review_count=0,
            image_url=img.get("src") if img else None,
            product_url=url, store=self.display_name,
        )

    async def supports_url(self, url: str) -> bool:
        return "zoodmall.uz" in url
