"""
Async HTTP client with retry logic, random user-agents, and headers
to reduce bot detection during scraping.
"""
from __future__ import annotations

import asyncio
import random
from typing import Optional

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from core.config import settings
from core.logging_config import get_logger

logger = get_logger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]


def get_random_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "uz-UZ,uz;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }


async def fetch_html(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    retries: int = None,
    timeout: int = None,
    session: Optional[ClientSession] = None,
) -> Optional[str]:
    """Fetch raw HTML from URL with retry logic."""
    retries = retries or settings.MAX_RETRIES
    timeout = timeout or settings.SCRAPE_TIMEOUT

    _headers = get_random_headers()
    if headers:
        _headers.update(headers)

    client_timeout = ClientTimeout(total=timeout)

    close_session = session is None
    if session is None:
        session = ClientSession(timeout=client_timeout)

    try:
        for attempt in range(retries):
            try:
                async with session.get(url, params=params, headers=_headers, ssl=False) as resp:
                    if resp.status == 200:
                        return await resp.text(errors="replace")
                    elif resp.status == 429:
                        wait = 2 ** attempt
                        logger.warning("rate_limited", url=url, attempt=attempt, wait=wait)
                        await asyncio.sleep(wait)
                    elif resp.status in (403, 404):
                        logger.warning("http_error", url=url, status=resp.status)
                        return None
                    else:
                        logger.warning("http_unexpected", url=url, status=resp.status)
                        await asyncio.sleep(1)
            except asyncio.TimeoutError:
                logger.warning("timeout", url=url, attempt=attempt)
                await asyncio.sleep(1)
            except aiohttp.ClientError as e:
                logger.warning("client_error", url=url, error=str(e), attempt=attempt)
                await asyncio.sleep(1)
    finally:
        if close_session:
            await session.close()

    return None


async def fetch_json(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    retries: int = None,
    timeout: int = None,
    session: Optional[ClientSession] = None,
) -> Optional[dict | list]:
    """Fetch JSON from URL with retry logic."""
    retries = retries or settings.MAX_RETRIES
    timeout = timeout or settings.SCRAPE_TIMEOUT

    _headers = get_random_headers()
    _headers["Accept"] = "application/json, text/plain, */*"
    if headers:
        _headers.update(headers)

    client_timeout = ClientTimeout(total=timeout)

    close_session = session is None
    if session is None:
        session = ClientSession(timeout=client_timeout)

    try:
        for attempt in range(retries):
            try:
                async with session.get(url, params=params, headers=_headers, ssl=False) as resp:
                    if resp.status == 200:
                        return await resp.json(content_type=None)
                    elif resp.status == 429:
                        wait = 2 ** attempt
                        await asyncio.sleep(wait)
                    else:
                        await asyncio.sleep(1)
            except asyncio.TimeoutError:
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning("json_fetch_error", url=url, error=str(e))
                await asyncio.sleep(1)
    finally:
        if close_session:
            await session.close()

    return None
