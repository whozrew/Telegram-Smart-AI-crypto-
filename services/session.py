"""
Search session manager.
Stores search results in Redis for paginated navigation.
"""
from __future__ import annotations

import json
import uuid
from typing import Optional

from services.cache import CacheService

_session_cache = CacheService(prefix="session")

SESSION_TTL = 3600  # 1 hour


async def create_search_session(
    user_id: int,
    results: list[dict],
    query: str,
) -> str:
    """Store search results in Redis and return session ID."""
    session_id = str(uuid.uuid4())[:8]
    payload = {
        "user_id": user_id,
        "query": query,
        "results": results,
        "compare_list": [],
    }
    await _session_cache.set(f"{session_id}", payload, ttl=SESSION_TTL)
    return session_id


async def get_search_session(session_id: str) -> Optional[dict]:
    """Retrieve session data."""
    return await _session_cache.get(session_id)


async def get_session_product(session_id: str, index: int) -> Optional[dict]:
    """Get a specific product from session results."""
    session = await get_search_session(session_id)
    if not session:
        return None
    results = session.get("results", [])
    if index < 0 or index >= len(results):
        return None
    return results[index]


async def add_to_compare(session_id: str, product_index: int) -> tuple[list[dict], bool]:
    """Add product to compare list. Returns (compare_list, added)."""
    session = await get_search_session(session_id)
    if not session:
        return [], False

    compare_list: list = session.get("compare_list", [])
    results = session.get("results", [])

    if product_index >= len(results):
        return compare_list, False

    product = results[product_index]
    # Avoid duplicates
    urls = [p.get("product_url") for p in compare_list]
    if product.get("product_url") in urls:
        return compare_list, False

    if len(compare_list) >= 5:
        return compare_list, False

    compare_list.append(product)
    session["compare_list"] = compare_list
    await _session_cache.set(session_id, session, ttl=SESSION_TTL)
    return compare_list, True


async def clear_compare(session_id: str) -> None:
    session = await get_search_session(session_id)
    if session:
        session["compare_list"] = []
        await _session_cache.set(session_id, session, ttl=SESSION_TTL)


async def get_compare_list(session_id: str) -> list[dict]:
    session = await get_search_session(session_id)
    if not session:
        return []
    return session.get("compare_list", [])
