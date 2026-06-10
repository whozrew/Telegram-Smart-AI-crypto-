"""
Halol Crypto AI - Market Data Scanner
Fetches OHLCV candles and price data. Caches aggressively. No API keys needed.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple

import aiohttp

from config import (
    BINANCE_BASE, COINGECKO_BASE, HALAL_COINS, COIN_SYMBOLS,
    CACHE_TTL_SECONDS, SIGNAL_CACHE_TTL, TIMEFRAMES,
)

logger = logging.getLogger(__name__)

# ─── Simple in-memory cache ───────────────────────────────────────────────────
_cache: Dict[str, Tuple[float, Any]] = {}


def _cache_get(key: str) -> Optional[Any]:
    entry = _cache.get(key)
    if entry and (time.time() - entry[0]) < CACHE_TTL_SECONDS:
        return entry[1]
    return None


def _cache_set(key: str, value: Any, ttl: int = CACHE_TTL_SECONDS) -> None:
    _cache[key] = (time.time(), value)


def _cache_get_ttl(key: str, ttl: int) -> Optional[Any]:
    entry = _cache.get(key)
    if entry and (time.time() - entry[0]) < ttl:
        return entry[1]
    return None


# ─── HTTP Session ─────────────────────────────────────────────────────────────

_session: Optional[aiohttp.ClientSession] = None


async def get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        timeout = aiohttp.ClientTimeout(total=15)
        _session = aiohttp.ClientSession(timeout=timeout)
    return _session


async def close_session() -> None:
    global _session
    if _session and not _session.closed:
        await _session.close()


# ─── Binance Data ─────────────────────────────────────────────────────────────

async def fetch_candles(
    symbol: str, timeframe: str = "4h", limit: int = 200
) -> List[Dict]:
    """Fetch OHLCV candles from Binance (no API key required for public data)."""
    cache_key = f"candles:{symbol}:{timeframe}:{limit}"
    cached = _cache_get_ttl(cache_key, SIGNAL_CACHE_TTL)
    if cached is not None:
        return cached

    # Binance uses BTCUSDT format
    pair = f"{symbol}USDT"
    tf   = TIMEFRAMES.get(timeframe, {}).get("kline", "4h")
    url  = f"{BINANCE_BASE}/klines"
    params = {"symbol": pair, "interval": tf, "limit": limit}

    try:
        session = await get_session()
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                logger.warning("Binance %s returned %s", pair, resp.status)
                return []
            data = await resp.json()
            candles = [
                {
                    "open":   float(k[1]),
                    "high":   float(k[2]),
                    "low":    float(k[3]),
                    "close":  float(k[4]),
                    "volume": float(k[5]),
                    "time":   k[0],
                }
                for k in data
            ]
            _cache_set(cache_key, candles, SIGNAL_CACHE_TTL)
            return candles
    except Exception as e:
        logger.error("fetch_candles %s %s: %s", symbol, timeframe, e)
        return []


async def fetch_ticker_24h(symbol: str) -> Dict:
    """24h price stats from Binance."""
    cache_key = f"ticker:{symbol}"
    cached = _cache_get_ttl(cache_key, 30)
    if cached:
        return cached

    pair = f"{symbol}USDT"
    url  = f"{BINANCE_BASE}/ticker/24hr"
    try:
        session = await get_session()
        async with session.get(url, params={"symbol": pair}) as resp:
            if resp.status != 200:
                return {}
            data = await resp.json()
            result = {
                "price":     float(data.get("lastPrice", 0)),
                "change_24h": float(data.get("priceChangePercent", 0)),
                "volume":    float(data.get("quoteVolume", 0)),
                "high_24h":  float(data.get("highPrice", 0)),
                "low_24h":   float(data.get("lowPrice", 0)),
            }
            _cache_set(cache_key, result, 30)
            return result
    except Exception as e:
        logger.error("fetch_ticker %s: %s", symbol, e)
        return {}


# ─── CoinGecko Data ───────────────────────────────────────────────────────────

async def fetch_market_overview() -> List[Dict]:
    """Fetch top market data from CoinGecko — no API key needed (rate limited)."""
    cache_key = "market_overview"
    cached = _cache_get_ttl(cache_key, 120)
    if cached:
        return cached

    cg_ids = [c["cg_id"] for c in HALAL_COINS]
    ids_str = ",".join(cg_ids[:20])  # CG free tier limit
    url = f"{COINGECKO_BASE}/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ids_str,
        "order": "market_cap_desc",
        "per_page": 20,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h",
    }
    try:
        session = await get_session()
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                logger.warning("CoinGecko market overview %s", resp.status)
                return _get_fallback_market()
            data = await resp.json()
            result = [
                {
                    "symbol":     d.get("symbol", "").upper(),
                    "name":       d.get("name", ""),
                    "price":      d.get("current_price", 0),
                    "change_24h": d.get("price_change_percentage_24h", 0),
                    "market_cap": d.get("market_cap", 0),
                    "volume":     d.get("total_volume", 0),
                    "rank":       d.get("market_cap_rank", 0),
                    "image":      d.get("image", ""),
                }
                for d in data
            ]
            _cache_set(cache_key, result, 120)
            return result
    except Exception as e:
        logger.error("fetch_market_overview: %s", e)
        return _get_fallback_market()


async def fetch_global_sentiment() -> Dict:
    """Global crypto market sentiment from CoinGecko."""
    cache_key = "global_sentiment"
    cached = _cache_get_ttl(cache_key, 300)
    if cached:
        return cached

    try:
        session = await get_session()
        async with session.get(f"{COINGECKO_BASE}/global") as resp:
            if resp.status != 200:
                return {"sentiment": "Neutral", "btc_dominance": 50}
            data = (await resp.json()).get("data", {})
            btc_dom = data.get("market_cap_percentage", {}).get("btc", 50)
            total_change = data.get("market_cap_change_percentage_24h_usd", 0)
            if total_change > 3:
                sentiment = "Very Bullish 🚀"
            elif total_change > 0:
                sentiment = "Bullish 📈"
            elif total_change > -3:
                sentiment = "Bearish 📉"
            else:
                sentiment = "Very Bearish 🔴"
            result = {
                "sentiment":       sentiment,
                "btc_dominance":   round(btc_dom, 1),
                "total_change_24h": round(total_change, 2),
                "active_coins":    data.get("active_cryptocurrencies", 0),
            }
            _cache_set(cache_key, result, 300)
            return result
    except Exception as e:
        logger.error("fetch_global_sentiment: %s", e)
        return {"sentiment": "Neutral", "btc_dominance": 50}


# ─── Multi-symbol batch fetch ─────────────────────────────────────────────────

async def fetch_prices_batch(symbols: List[str]) -> Dict[str, Dict]:
    """Fetch prices for multiple symbols concurrently."""
    tasks = [fetch_ticker_24h(s) for s in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {
        sym: res if isinstance(res, dict) else {}
        for sym, res in zip(symbols, results)
    }


async def fetch_watchlist_data(symbols: List[str]) -> List[Dict]:
    """Fetch price + basic data for watchlist display."""
    prices = await fetch_prices_batch(symbols)
    result = []
    for sym in symbols:
        coin_info = COIN_SYMBOLS.get(sym, {"name": sym, "symbol": sym})
        price_data = prices.get(sym, {})
        result.append({
            "symbol":   sym,
            "name":     coin_info.get("name", sym),
            "price":    price_data.get("price", 0),
            "change":   price_data.get("change_24h", 0),
            "volume":   price_data.get("volume", 0),
        })
    return result


# ─── Fallback data ────────────────────────────────────────────────────────────

def _get_fallback_market() -> List[Dict]:
    """Static fallback if API is down."""
    return [
        {"symbol": c["symbol"], "name": c["name"], "price": 0,
         "change_24h": 0, "market_cap": 0, "volume": 0, "rank": i + 1}
        for i, c in enumerate(HALAL_COINS[:10])
    ]
