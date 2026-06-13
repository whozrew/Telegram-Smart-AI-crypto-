# Online Bozor Narxlari — Deployment Guide

## Overview

Production-ready Telegram bot for comparing product prices across Uzbekistan and global marketplaces.

- **13 marketplace providers** (Uzum, OLX, Asaxiy, MediaPark, Texnomart, Idea, Goodzone, ZoodMall, AliExpress, Amazon, eBay, Temu, Wildberries)
- **AI advice** via Google Gemini
- **OCR** — extract product name from screenshots
- **Price alerts** — background scheduler notifies users when target price is reached
- **Multilingual** — Uzbek, Russian, English with auto-detection
- **Redis caching** — blazing fast repeated searches
- **PostgreSQL** — full relational data storage

---

## Project Structure

```
bozor_narxlari/
├── main.py                      # Entry point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── railway.json
├── alembic.ini
├── .env.example
│
├── core/
│   ├── config.py                # Pydantic settings
│   └── logging_config.py        # Structured logging
│
├── database/
│   ├── db.py                    # Engine, session factory
│   ├── models.py                # All ORM models
│   └── migrations/
│       ├── env.py               # Alembic async env
│       ├── script.py.mako
│       └── versions/
│           └── 001_initial.py   # Initial migration
│
├── providers/
│   ├── __init__.py              # Registry + fan-out search
│   ├── base.py                  # BaseProvider + ProductResult
│   ├── uzum.py                  # Uzum.uz
│   ├── olx.py                   # OLX Uzbekistan
│   ├── asaxiy.py                # Asaxiy.uz
│   ├── uzbek_stores.py          # MediaPark, Texnomart, Idea, Goodzone, ZoodMall
│   └── global_stores.py         # AliExpress, Amazon, eBay, Temu, Wildberries
│
├── services/
│   ├── cache.py                 # Redis cache service
│   ├── search.py                # Search orchestration + fuzzy matching
│   ├── user.py                  # User CRUD + stats
│   ├── favorites.py             # Favorites, Watchlist, Alerts
│   ├── gemini.py                # Gemini AI + OCR
│   ├── session.py               # Search result sessions (Redis)
│   └── scheduler.py             # Background price alert checker
│
├── bot/
│   ├── handlers/
│   │   ├── start.py             # /start, /help, /language, /settings
│   │   ├── search.py            # Text/URL search, product cards, navigation
│   │   ├── ocr.py               # Photo → OCR → search
│   │   ├── favorites.py         # /favorites management
│   │   ├── watchlist.py         # /watchlist management
│   │   ├── alerts.py            # Price alerts setup + management
│   │   └── admin.py             # Admin panel, broadcast, ban/unban
│   ├── keyboards/
│   │   └── __init__.py          # All inline + reply keyboards
│   ├── middlewares/
│   │   └── __init__.py          # UserContext, BanCheck, AntiSpam
│   └── filters/
│       └── __init__.py          # IsAdmin, IsNotBanned
│
└── utils/
    ├── i18n.py                  # Full translation system (uz/ru/en)
    └── http_client.py           # Async HTTP with retry + user-agent rotation
```

---

## Quick Start (Local)

### 1. Clone and prepare

```bash
git clone <your-repo>
cd bozor_narxlari
cp .env.example .env
# Edit .env with your values
```

### 2. Fill in .env

```env
BOT_TOKEN=your_bot_token_from_botfather
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/bozor_narxlari
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=your_gemini_api_key
ADMIN_IDS=your_telegram_user_id
MAX_ACTIVE_USERS=1000
```

### 3. Start with Docker Compose

```bash
docker compose up -d
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **Migrator** (runs `alembic upgrade head` once)
- **Bot** (starts after DB is ready)

### 4. View logs

```bash
docker compose logs -f bot
```

---

## Railway Deployment

### Step 1 — Create Railway project

```bash
npm install -g @railway/cli
railway login
railway init
```

### Step 2 — Add services

In Railway dashboard, add:
1. **PostgreSQL** plugin
2. **Redis** plugin
3. **Your repo** as a service

### Step 3 — Set environment variables

In Railway → your service → Variables, add all keys from `.env.example`:

| Variable | Value |
|---|---|
| `BOT_TOKEN` | Your Telegram bot token |
| `DATABASE_URL` | Auto-filled by Railway PostgreSQL plugin |
| `REDIS_URL` | Auto-filled by Railway Redis plugin |
| `GEMINI_API_KEY` | From Google AI Studio |
| `ADMIN_IDS` | Your Telegram user ID(s), comma-separated |
| `MAX_ACTIVE_USERS` | `1000` |
| `LOG_LEVEL` | `INFO` |
| `ENVIRONMENT` | `production` |
| `CACHE_TTL` | `3600` |

### Step 4 — Deploy

```bash
railway up
```

Railway reads `railway.json` which runs:
```
alembic upgrade head && python main.py
```

### Step 5 — Verify

```bash
railway logs
```

---

## Manual Setup (Without Docker)

### Prerequisites

- Python 3.13+
- PostgreSQL 15+
- Redis 7+

### Install dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### Initialize database

```bash
alembic upgrade head
```

### Run

```bash
python main.py
```

---

## Getting API Keys

### Telegram Bot Token
1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/newbot`
3. Follow instructions
4. Copy the token to `BOT_TOKEN`

### Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click **Get API key**
3. Create a new key (free tier available)
4. Copy to `GEMINI_API_KEY`

### Your Telegram User ID
1. Open [@userinfobot](https://t.me/userinfobot) in Telegram
2. Send `/start`
3. Copy your numeric ID to `ADMIN_IDS`

---

## Adding New Providers

Create a new file in `providers/`:

```python
# providers/mynewstore.py
from providers.base import BaseProvider, ProductResult

class MyNewStoreProvider(BaseProvider):
    name = "mynewstore"
    display_name = "My New Store"
    base_url = "https://mynewstore.com"
    is_uzbek = True  # or False for global

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        # Implement search logic
        ...

    async def get_product(self, url: str) -> ProductResult | None:
        # Implement single product fetch
        ...

    async def supports_url(self, url: str) -> bool:
        return "mynewstore.com" in url
```

Then register it in `providers/__init__.py`:

```python
from providers.mynewstore import MyNewStoreProvider
# ...inside _register_defaults():
self.register(MyNewStoreProvider())
```

**No other code changes needed.** The provider is automatically included in all searches.

---

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Start or restart the bot |
| `/search` | Search for a product |
| `/favorites` | View saved products |
| `/watchlist` | View tracked products |
| `/alerts` | Manage price alerts |
| `/language` | Change language |
| `/settings` | Settings menu |
| `/help` | Help and usage guide |
| `/admin` | Admin panel (admins only) |

---

## Admin Panel Features

Access via `/admin` command (admin IDs only):

- **📊 Statistics** — total users, active users, total searches, active alerts, favorites, banned count
- **📢 Broadcast** — send text/photo/video/document to all active users
- **🚫 Ban User** — ban by user ID
- **✅ Unban User** — unban by user ID

---

## Architecture Notes

### Search Flow

```
User message
    ↓
AntiSpam Middleware (rate limit check)
BanCheck Middleware (ban check)
UserContext Middleware (load/create user, attach lang)
    ↓
Handler detects: text / URL / photo
    ↓
search_service.search_auto()
    ↓
ProviderRegistry.search_all() ← fan-out to all 13 providers concurrently
    ↓
Fuzzy match → split exact/similar
    ↓
Create Redis session (stores all results by session_id)
    ↓
Send product card with inline keyboard
    ↓
User navigates ⬅/➡ → loads from Redis session (no re-scraping)
```

### Price Alert Flow

```
Background scheduler (every PRICE_CHECK_INTERVAL seconds)
    ↓
Load all active alerts from DB
    ↓
For each alert: re-scrape current price via provider
    ↓
Compare current price vs target_price
    ↓
If price <= target: send Telegram notification, deactivate alert
```

### Cache Strategy

- **Search results**: cached in Redis by query hash for `SEARCH_CACHE_TTL` seconds
- **User sessions**: paginated search results stored in Redis for 1 hour
- **Ban status**: cached per user for 5 minutes to reduce DB hits
- **Rate limiting**: per-user message count tracked in Redis with TTL window

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `BOT_TOKEN` | required | Telegram bot token |
| `DATABASE_URL` | required | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `GEMINI_API_KEY` | required | Google Gemini API key |
| `ADMIN_IDS` | `""` | Comma-separated admin Telegram IDs |
| `MAX_ACTIVE_USERS` | `1000` | Max concurrent users (new users blocked above limit) |
| `CACHE_TTL` | `3600` | Default cache TTL in seconds |
| `SEARCH_CACHE_TTL` | `1800` | Search result cache TTL |
| `PRICE_CACHE_TTL` | `900` | Price data cache TTL |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_FILE` | `logs/bot.log` | Log file path |
| `RATE_LIMIT_MESSAGES` | `5` | Max messages per user per window |
| `RATE_LIMIT_PERIOD` | `60` | Rate limit window in seconds |
| `SEARCH_COOLDOWN` | `3` | Seconds between searches per user |
| `SCRAPE_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `MAX_RETRIES` | `3` | HTTP retry attempts |
| `RESULTS_PER_PAGE` | `5` | Results per page |
| `MAX_RESULTS` | `50` | Max total results per search |
| `PRICE_CHECK_INTERVAL` | `3600` | Alert check interval in seconds |
| `ALERT_BATCH_SIZE` | `100` | Alerts processed per batch |
| `DEBUG` | `false` | Enable debug mode (verbose SQL, etc.) |
| `ENVIRONMENT` | `production` | Environment (`production` / `development`) |

---

## Scaling Notes

- **Horizontal scaling**: The bot is stateless (session in Redis). Run multiple instances safely.
- **Provider timeouts**: Each search has a 20s hard timeout. Slow providers are skipped automatically.
- **DB pool**: `pool_size=10, max_overflow=20` — handles 30 concurrent DB connections.
- **Redis TTL**: All cached data has TTL. Redis memory is bounded to 256MB in docker-compose.
- **Broadcast rate limiting**: Respects Telegram's 30 msg/sec limit automatically.
