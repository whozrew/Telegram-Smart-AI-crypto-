"""
Halol Crypto AI - Configuration
All settings loaded from environment variables with sensible defaults.
"""

import os
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ─── Telegram ─────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
WEBAPP_URL: str = os.getenv("WEBAPP_URL", "https://your-domain.com")

# ─── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/halol.db")

# ─── Server ───────────────────────────────────────────────────────────────────
WEBAPP_HOST: str = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT: int = int(os.getenv("WEBAPP_PORT", "8080"))
WEBHOOK_PATH: str = "/webhook"
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")  # Full URL for webhook mode

# ─── Market Data ──────────────────────────────────────────────────────────────
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
BINANCE_BASE = "https://api.binance.com/api/v3"
CACHE_TTL_SECONDS: int = 60          # Market data cache
SIGNAL_CACHE_TTL: int = 300          # Signal cache (5 min)
SCANNER_INTERVAL: int = 300          # Background scanner (5 min)

# ─── Halal Coins ──────────────────────────────────────────────────────────────
# Only halal spot assets — no stable-only, no memecoins with no utility
HALAL_COINS = [
    {"symbol": "BTC",  "name": "Bitcoin",         "cg_id": "bitcoin"},
    {"symbol": "ETH",  "name": "Ethereum",         "cg_id": "ethereum"},
    {"symbol": "BNB",  "name": "BNB",              "cg_id": "binancecoin"},
    {"symbol": "SOL",  "name": "Solana",           "cg_id": "solana"},
    {"symbol": "ADA",  "name": "Cardano",          "cg_id": "cardano"},
    {"symbol": "XRP",  "name": "XRP",              "cg_id": "ripple"},
    {"symbol": "DOT",  "name": "Polkadot",         "cg_id": "polkadot"},
    {"symbol": "LINK", "name": "Chainlink",        "cg_id": "chainlink"},
    {"symbol": "AVAX", "name": "Avalanche",        "cg_id": "avalanche-2"},
    {"symbol": "MATIC","name": "Polygon",          "cg_id": "matic-network"},
    {"symbol": "TON",  "name": "Toncoin",          "cg_id": "the-open-network"},
    {"symbol": "ATOM", "name": "Cosmos",           "cg_id": "cosmos"},
    {"symbol": "UNI",  "name": "Uniswap",          "cg_id": "uniswap"},
    {"symbol": "LTC",  "name": "Litecoin",         "cg_id": "litecoin"},
    {"symbol": "NEAR", "name": "NEAR Protocol",    "cg_id": "near"},
    {"symbol": "APT",  "name": "Aptos",            "cg_id": "aptos"},
    {"symbol": "ARB",  "name": "Arbitrum",         "cg_id": "arbitrum"},
    {"symbol": "OP",   "name": "Optimism",         "cg_id": "optimism"},
    {"symbol": "SUI",  "name": "Sui",              "cg_id": "sui"},
    {"symbol": "INJ",  "name": "Injective",        "cg_id": "injective-protocol"},
    {"symbol": "TIA",  "name": "Celestia",         "cg_id": "celestia"},
    {"symbol": "SEI",  "name": "Sei",              "cg_id": "sei-network"},
    {"symbol": "FTM",  "name": "Fantom",           "cg_id": "fantom"},
    {"symbol": "ALGO", "name": "Algorand",         "cg_id": "algorand"},
    {"symbol": "VET",  "name": "VeChain",          "cg_id": "vechain"},
]

COIN_SYMBOLS = {c["symbol"]: c for c in HALAL_COINS}
COIN_CG_IDS  = {c["cg_id"]:  c for c in HALAL_COINS}

# ─── Timeframes ───────────────────────────────────────────────────────────────
TIMEFRAMES = {
    "15m": {"label": "15 Minutes", "kline": "15m",  "limit": 200},
    "1h":  {"label": "1 Hour",     "kline": "1h",   "limit": 200},
    "4h":  {"label": "4 Hours",    "kline": "4h",   "limit": 200},
    "1d":  {"label": "1 Day",      "kline": "1d",   "limit": 200},
}

# ─── Signal Thresholds ────────────────────────────────────────────────────────
STRONG_BUY_THRESHOLD = 75
BUY_THRESHOLD        = 55
WAIT_THRESHOLD       = 40
# Below WAIT_THRESHOLD → Profit Taking Zone

# ─── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE  = LOG_DIR / "halol.log"
