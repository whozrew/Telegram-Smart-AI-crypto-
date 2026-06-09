import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Barcha zaruriy texnik indikatorlarni hisoblash paneli"""
    if len(df) < 200:
        return df

    # EMA tizimi
    df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()

    # RSI hisoblash
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-10)
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD line va Signal line
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # ATR va Bollinger Bands
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['ATR'] = true_range.rolling(14).mean()
    
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    df['BB_std'] = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
    df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)

    # ADX (Trend kuchi)
    plus_dm = df['high'].diff()
    minus_dm = df['low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    minus_dm = np.abs(minus_dm)
    
    tr_smooth = true_range.rolling(window=14).sum()
    plus_di = 100 * (plus_dm.rolling(window=14).sum() / (tr_smooth + 1e-10))
    minus_di = 100 * (minus_dm.rolling(window=14).sum() / (tr_smooth + 1e-10))
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    df['ADX'] = dx.rolling(window=14).mean()

    # Support va Resistance darajalari (Yaqindagi 20 shamlik ekstremumlar)
    df['Support'] = df['low'].rolling(window=20).min()
    df['Resistance'] = df['high'].rolling(window=20).max()

    return df

def detect_smc_and_advanced(df: pd.DataFrame) -> Dict[str, Any]:
    """Smart Money Concepts va Murakkab Price Action tuzilmalarini aniqlash"""
    last_idx = df.index[-1]
    prev_idx = df.index[-2]
    prev2_idx = df.index[-3]
    
    analysis = {
        "fvg_bullish": False, "fvg_bearish": False,
        "order_block_bullish": False, "order_block_bearish": False,
        "bos": False, "choch": False,
        "liquidity_sweep_bullish": False, "liquidity_sweep_bearish": False,
        "breakout_retest": False, "rvol": 1.0
    }

    # 1. Fair Value Gap (FVG)
    if df.loc[prev2_idx, 'high'] < df.loc[last_idx, 'low']:
        analysis["fvg_bullish"] = True
    elif df.loc[prev2_idx, 'low'] > df.loc[last_idx, 'high']:
        analysis["fvg_bearish"] = True

    # 2. Order Blocks (OB) va Market Structure (BOS / CHoCH)
    # Oxirgi sham yopilish narxi oldingi qarshilikni buzganda (BOS)
    if df.loc[last_idx, 'close'] > df.loc[prev_idx, 'Resistance']:
        analysis["bos"] = True
        if df.loc[prev_idx, 'close'] <= df.loc[prev_idx, 'Resistance']:
            analysis["choch"] = True
        # Oxirgi ko'tarilishdan oldingi tushish shami OB hisoblanadi
        if df.loc[prev_idx, 'close'] < df.loc[prev_idx, 'open']:
            analysis["order_block_bullish"] = True

    if df.loc[last_idx, 'close'] < df.loc[prev_idx, 'Support']:
        if df.loc[prev_idx, 'close'] >= df.loc[prev_idx, 'open']:
            analysis["order_block_bearish"] = True

    # 3. Liquidity Sweep (Stop Hunt aniqlash logikasi)
    # Agar narx support ostiga tushib, lekin tezda ko'tarilib support tepasida yopilsa (Wick hosil qilsa)
    if df.loc[last_idx, 'low'] < df.loc[prev_idx, 'Support'] and df.loc[last_idx, 'close'] > df.loc[prev_idx, 'Support']:
        analysis["liquidity_sweep_bullish"] = True
    if df.loc[last_idx, 'high'] > df.loc[prev_idx, 'Resistance'] and df.loc[last_idx, 'close'] < df.loc[prev_idx, 'Resistance']:
        analysis["liquidity_sweep_bearish"] = True

    # 4. Breakout + Retest Detection
    # Buzib o'tilgan darajaga qaytib kelib, uni qo'llab-quvvatlash sifatida tasdiqlashi
    if df.loc[prev_idx, 'close'] > df.loc[prev2_idx, 'Resistance'] and np.abs(df.loc[last_idx, 'low'] - df.loc[prev2_idx, 'Resistance']) / df.loc[last_idx, 'close'] < 0.01:
        if df.loc[last_idx, 'close'] > df.loc[last_idx, 'open']:
            analysis["breakout_retest"] = True

    # 5. Relative Volume (RVOL) hisoblash
    avg_volume = df['volume'].rolling(window=24).mean().iloc[-1]
    current_volume = df['volume'].iloc[-1]
    analysis["rvol"] = current_volume / (avg_volume + 1e-10)

    return analysis
