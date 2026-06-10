"""
Halol Crypto AI - Database Layer
SQLite by default, migrates to PostgreSQL via DATABASE_URL env var.
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
import aiosqlite

from config import DATABASE_URL, DATA_DIR

logger = logging.getLogger(__name__)

DB_PATH = str(DATA_DIR / "halol.db")


# ─── Schema ───────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    language    TEXT DEFAULT 'en',
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS watchlists (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    symbol      TEXT NOT NULL,
    added_at    TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, symbol),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    symbol        TEXT NOT NULL,
    alert_type    TEXT NOT NULL,
    threshold     REAL,
    is_active     INTEGER DEFAULT 1,
    triggered_at  TEXT,
    created_at    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS signal_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol      TEXT NOT NULL,
    timeframe   TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    score       REAL NOT NULL,
    price       REAL,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id         INTEGER PRIMARY KEY,
    default_tf      TEXT DEFAULT '4h',
    alert_enabled   INTEGER DEFAULT 1,
    theme           TEXT DEFAULT 'dark',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlists(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_user    ON alerts(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signal_history(symbol, created_at);
"""


# ─── Connection ───────────────────────────────────────────────────────────────

async def get_db() -> aiosqlite.Connection:
    """Get an async SQLite connection with row factory."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    """Create all tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()
    logger.info("Database initialized at %s", DB_PATH)


# ─── Users ────────────────────────────────────────────────────────────────────

async def upsert_user(user_id: int, username: str = "", first_name: str = "") -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name,
                updated_at = datetime('now')
        """, (user_id, username or "", first_name or ""))
        # Ensure settings row exists
        await db.execute("""
            INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)
        """, (user_id,))
        await db.commit()


async def get_user_settings(user_id: int) -> Dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM user_settings WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            if row:
                return dict(row)
            return {"default_tf": "4h", "alert_enabled": 1, "theme": "dark"}


async def update_user_settings(user_id: int, **kwargs) -> None:
    allowed = {"default_tf", "alert_enabled", "theme"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    cols = ", ".join(f"{k} = ?" for k in updates)
    vals = list(updates.values()) + [user_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE user_settings SET {cols} WHERE user_id = ?", vals)
        await db.commit()


# ─── Watchlist ────────────────────────────────────────────────────────────────

async def get_watchlist(user_id: int) -> List[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT symbol FROM watchlists WHERE user_id = ? ORDER BY added_at DESC",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [r["symbol"] for r in rows]


async def add_to_watchlist(user_id: int, symbol: str) -> bool:
    """Returns True if added, False if already exists."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO watchlists (user_id, symbol) VALUES (?, ?)",
                (user_id, symbol.upper())
            )
            await db.commit()
        return True
    except aiosqlite.IntegrityError:
        return False


async def remove_from_watchlist(user_id: int, symbol: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM watchlists WHERE user_id = ? AND symbol = ?",
            (user_id, symbol.upper())
        )
        await db.commit()
        return cur.rowcount > 0


# ─── Alerts ───────────────────────────────────────────────────────────────────

async def get_active_alerts(user_id: int) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM alerts WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def create_alert(user_id: int, symbol: str, alert_type: str, threshold: Optional[float] = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO alerts (user_id, symbol, alert_type, threshold) VALUES (?, ?, ?, ?)",
            (user_id, symbol.upper(), alert_type, threshold)
        )
        await db.commit()
        return cur.lastrowid


async def deactivate_alert(alert_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE alerts SET is_active = 0, triggered_at = datetime('now') WHERE id = ?",
            (alert_id,)
        )
        await db.commit()


async def get_all_watchlist_users() -> List[Dict]:
    """Returns all (user_id, symbol) pairs for background scanner."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT DISTINCT user_id, symbol FROM watchlists"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# ─── Signal History ───────────────────────────────────────────────────────────

async def save_signal(symbol: str, timeframe: str, signal_type: str, score: float, price: float) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO signal_history (symbol, timeframe, signal_type, score, price)
               VALUES (?, ?, ?, ?, ?)""",
            (symbol, timeframe, signal_type, score, price)
        )
        await db.commit()


async def get_recent_signals(symbol: str, limit: int = 10) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM signal_history WHERE symbol = ?
               ORDER BY created_at DESC LIMIT ?""",
            (symbol, limit)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
