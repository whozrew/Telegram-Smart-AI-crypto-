import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Tizim Sozlamalari
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "600"))  # Soniyalarda (10 daqiqa)
ALERT_THRESHOLD = int(os.getenv("ALERT_THRESHOLD", "80"))  # Kuchli signal chegarasi
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Binance API Base URL (Spot Market ochiq ma'lumotlari uchun API kalit shart emas)
BINANCE_BASE_URL = "https://api.binance.com"

# Halol Spot Coinlar Ro'yxati (Taxminan 100 ta eng likvidli va halol deb topilgan aktivlar)
HALAL_COINS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "AVAXUSDT", "ADAUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "UNIUSDT", "LTCUSDT", "ATOMUSDT", "XLMUSDT", "ALGOUSDT", "VETUSDT", "ICPUSDT",
    "FILUSDT", "AAVEUSDT", "GRTUSDT", "STXUSDT", "EGLDUSDT", "SANDUSDT", "MANAUSDT", "THETAUSDT",
    "CHZUSDT", "GALAUSDT", "ONEUSDT", "ENJUSDT", "LRCUSDT", "ANKRUSDT", "BATUSDT", "ZILUSDT",
    "FTMUSDT", "NEARUSDT", "CRVUSDT", "AXSUSDT", "IMXUSDT", "FLOWUSDT", "APEUSDT", "RUNEUSDT",
    "CELOUSDT", "MINAUSDT", "WOOUSDT", "KAVAUSDT", "JSTUSDT", "SUNUSDT", "OCEANUSDT", "ROSEUSDT",
    "DGBUSDT", "RVNUSDT", "AUDIOUSDT", "HOTUSDT", "QTUMUSDT", "ONTUSDT", "ZRXUSDT", "IOSTUSDT",
    "SXPUSDT", "OGNUSDT", "FETUSDT", "AGIXUSDT", "OCEANUSDT", "RLCUSDT", "NMRUSDT", "BANDUSDT",
    "CTSIUSDT", "STMXUSDT", "RENUSDT", "TOMOUSDT", "DENTUSDT", "KEYUSDT", "MFTUSDT", "DATAUSDT",
    "OXTUSDT", "STPTUSDT", "WRXUSDT", "UTKUSDT", "CHRUSDT", "COCOSDT", "MTLUSDT", "ALICEDUSDT",
    "C98USDT", "RAYUSDT", "DYDXUSDT", "GALAUSDT", "ENSUSDT", "JASMYUSDT", "AMPUSDT", "PLAUSDT",
    "VOXELUSDT", "HIGHUSDT", "GLMRUSDT", "ASTRUSDT", "ACHUSDT", "FITFIUSDT", "GALUSDT", "LDOUSDT"
]

# Taqqiqlangan va shubhali tokenlar filtri (Leveraged, Futures short yoki pump-dump belgilari borlar)
BANNED_TOKENS = ["DOWNUSDT", "UPUSDT", "BULLUSDT", "BEARUSDT"]
HALAL_COINS = [coin for coin in HALAL_COINS if coin not in BANNED_TOKENS]
