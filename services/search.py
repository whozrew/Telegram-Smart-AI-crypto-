"""
Search service.
Handles text search, URL search, fuzzy matching, and result caching.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Optional
from urllib.parse import urlparse

from providers import registry
from providers.base import ProductResult
from services.cache import search_cache
from core.config import settings
from core.logging_config import get_logger

logger = get_logger(__name__)

try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logger.warning("rapidfuzz_not_available", msg="Install rapidfuzz for fuzzy matching")


def _make_cache_key(query: str, search_type: str = "text") -> str:
    normalized = query.lower().strip()
    return hashlib.md5(f"{search_type}:{normalized}".encode()).hexdigest()


def _is_url(text: str) -> bool:
    try:
        parsed = urlparse(text.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _normalize_query(query: str) -> str:
    """Clean and normalize search query."""
    query = query.strip()
    query = re.sub(r"\s+", " ", query)
    return query


def _split_results(
    results: list[ProductResult], query: str
) -> tuple[list[ProductResult], list[ProductResult]]:
    """
    Split results into exact matches and similar products.
    Uses fuzzy matching if available, otherwise simple substring matching.
    """
    query_lower = query.lower()
    exact: list[ProductResult] = []
    similar: list[ProductResult] = []

    for product in results:
        title_lower = product.title.lower()
        if FUZZY_AVAILABLE:
            score = fuzz.token_set_ratio(query_lower, title_lower)
            if score >= 80:
                exact.append(product)
            elif score >= 50:
                similar.append(product)
        else:
            # Simple substring match fallback
            words = query_lower.split()
            match_count = sum(1 for w in words if w in title_lower)
            ratio = match_count / len(words) if words else 0
            if ratio >= 0.8:
                exact.append(product)
            elif ratio >= 0.4:
                similar.append(product)

    return exact, similar


class SearchService:
    async def search_by_text(
        self,
        query: str,
        user_id: Optional[int] = None,
        max_results: int = None,
    ) -> dict:
        """
        Search by text query.
        Returns dict with 'exact', 'similar', 'all', 'query', 'cached'.
        """
        query = _normalize_query(query)
        max_results = max_results or settings.MAX_RESULTS
        cache_key = _make_cache_key(query)

        # Check cache
        cached = await search_cache.get(cache_key)
        if cached:
            logger.info("search_cache_hit", query=query)
            return {**cached, "cached": True}

        logger.info("search_text", query=query, user_id=user_id)

        results = await registry.search_all(
            query=query,
            max_results_per_provider=max(5, max_results // len(registry.all_providers) + 1),
            timeout=20.0,
        )

        exact, similar = _split_results(results, query)

        payload = {
            "query": query,
            "exact": [r.to_dict() for r in exact[:max_results]],
            "similar": [r.to_dict() for r in similar[:max_results]],
            "all": [r.to_dict() for r in results[:max_results]],
            "total": len(results),
            "cached": False,
        }

        # Cache the result
        await search_cache.set(cache_key, payload, ttl=settings.SEARCH_CACHE_TTL)

        return payload

    async def search_by_url(self, url: str, user_id: Optional[int] = None) -> Optional[dict]:
        """Search / fetch a product by URL."""
        url = url.strip()
        if not _is_url(url):
            return None

        cache_key = _make_cache_key(url, "url")
        cached = await search_cache.get(cache_key)
        if cached:
            return {**cached, "cached": True}

        logger.info("search_url", url=url, user_id=user_id)
        product = await registry.get_product_by_url(url)
        if not product:
            return None

        payload = {
            "query": url,
            "exact": [product.to_dict()],
            "similar": [],
            "all": [product.to_dict()],
            "total": 1,
            "cached": False,
        }
        await search_cache.set(cache_key, payload, ttl=settings.SEARCH_CACHE_TTL)
        return payload

    async def search_auto(
        self, text: str, user_id: Optional[int] = None
    ) -> dict:
        """Automatically determine if text is a URL or query and search."""
        text = text.strip()
        if _is_url(text):
            result = await self.search_by_url(text, user_id)
            if result:
                return result
            # Fallback to text search with domain-based query
            query = urlparse(text).netloc.replace("www.", "")
            return await self.search_by_text(query, user_id)
        return await self.search_by_text(text, user_id)


search_service = SearchService()
