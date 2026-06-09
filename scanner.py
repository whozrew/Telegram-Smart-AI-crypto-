import asyncio
import logging
import requests
import pandas as pd
from typing import Dict, List, Any
from config import BINANCE_BASE_URL, HALAL_COINS
from utils import calculate_indicators
from signals import generate_trading_signal

logger = logging.getLogger(__name__)

# Kesh tizimi global o'zgaruvchilari
market_cache: Dict[str, Any] = {}
cached_rankings: Dict[str, Any] = {}

async def fetch_klines(coin: str, timeframe: str, limit: int = 250) -> pd.DataFrame:
    """Binance ochiq API-sidan shamlar tarixini xavfsiz yuklash"""
    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    params = {"symbol": coin, "interval": timeframe, "limit": limit}
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.get(url, params=params, timeout=10))
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'count', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            return df
        else:
            logger.error(f"Binance API xatolik: {response.status_code} {coin}")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Klines yuklashda xatolik {coin}: {str(e)}")
        return pd.DataFrame()

async def analyze_single_coin(coin: str) -> Dict[str, Any]:
    """Bitta aktivni bir nechta timeframe-da kompleks tahlil qilish"""
    df_1h = await fetch_klines(coin, '1h')
    df_4h = await fetch_klines(coin, '4h')
    
    if df_1h.empty or df_4h.empty:
        return {}

    df_1h = calculate_indicators(df_1h)
    df_4h = calculate_indicators(df_4h)

    frames = {'1h': df_1h, '4h': df_4h}
    signal_results = generate_trading_signal(frames, coin)
    
    # Global keshni yangilash
    market_cache[coin] = {
        "df_1h": df_1h,
        "signal_data": signal_results
    }
    return signal_results

async def run_market_scanner_loop(bot_instance=None):
    """Barcha halol coinlarni doimiy ravishda monitoring qiluvchi dvigatel"""
    while True:
        logger.info("Bozor skaneri ishga tushdi...")
        all_signals = []
        
        for coin in HALAL_COINS:
            res = await analyze_single_coin(coin)
            if res and "signal" in res:
                all_signals.append({"coin": coin, **res})
                
                # Agar signal shurdoq 'KUCHLI' bo'lsa va bot obyekti mavjud bo'lsa, alert jo'natish logikasini shu yerda ochish mumkin
                if res["score"] >= 80 and bot_instance:
                    pass # bot.py ichidagi tizim orqali push jo'natiladi
            await asyncio.sleep(0.2) # Rate limitga tushmaslik uchun preventiv pauza

        # Reytinglarni yangilash va saralash
        if all_signals:
            top_trending = sorted(all_signals, key=lambda x: x['score'], reverse=True)[:10]
            highest_vol = sorted(all_signals, key=lambda x: x['entry_quality'], reverse=True)[:10]
            
            cached_rankings['top_opportunities'] = top_trending
            cached_rankings['highest_volume'] = highest_vol
            
        logger.info("Skanerlash yakunlandi. 10 daqiqalik uyqu rejimiga o'tilmoqda.")
        await asyncio.sleep(600)
