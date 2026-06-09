import sqlite3
from typing import List, Tuple, Dict, Any

DB_NAME = "halal_crypto_bot.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    
    # Watchlist (Kuzatuv ro'yxati) jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watchlists (
        user_id INTEGER,
        coin TEXT,
        PRIMARY KEY (user_id, coin)
    )""")
    
    # Signallar tarixi jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS signal_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coin TEXT,
        signal_type TEXT,
        confidence_score INTEGER,
        entry_price REAL,
        stop_loss REAL,
        tp1 REAL,
        tp2 REAL,
        tp3 REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    
    conn.commit()
    conn.close()

def add_user(user_id: int, username: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def add_to_watchlist(user_id: int, coin: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO watchlists (user_id, coin) VALUES (?, ?)", (user_id, coin.upper()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_watchlist(user_id: int) -> List[str]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT coin FROM watchlists WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def remove_from_watchlist(user_id: int, coin: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlists WHERE user_id = ? AND coin = ?", (user_id, coin.upper()))
    changes = conn.total_changes
    conn.commit()
    conn.close()
    return changes > 0

def log_signal(coin: str, s_type: str, score: int, entry: float, sl: float, tp1: float, tp2: float, tp3: float):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO signal_history (coin, signal_type, confidence_score, entry_price, stop_loss, tp1, tp2, tp3)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (coin, s_type, score, entry, sl, tp1, tp2, tp3))
    conn.commit()
    conn.close()
