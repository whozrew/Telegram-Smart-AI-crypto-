"""
Halol Crypto AI - Technical Indicators
Pure Python calculations — no TA-Lib dependency for portability.
"""

import math
import logging
from typing import List, Optional, Tuple, Dict

logger = logging.getLogger(__name__)


# ─── Moving Averages ──────────────────────────────────────────────────────────

def ema(values: List[float], period: int) -> List[Optional[float]]:
    """Exponential Moving Average."""
    result: List[Optional[float]] = [None] * len(values)
    if len(values) < period:
        return result
    k = 2 / (period + 1)
    # Seed with SMA of first `period` values
    seed = sum(values[:period]) / period
    result[period - 1] = seed
    for i in range(period, len(values)):
        result[i] = values[i] * k + result[i - 1] * (1 - k)
    return result


def sma(values: List[float], period: int) -> List[Optional[float]]:
    """Simple Moving Average."""
    result: List[Optional[float]] = [None] * len(values)
    for i in range(period - 1, len(values)):
        result[i] = sum(values[i - period + 1: i + 1]) / period
    return result


# ─── RSI ──────────────────────────────────────────────────────────────────────

def rsi(values: List[float], period: int = 14) -> List[Optional[float]]:
    """Relative Strength Index."""
    result: List[Optional[float]] = [None] * len(values)
    if len(values) < period + 1:
        return result
    gains, losses = [], []
    for i in range(1, len(values)):
        diff = values[i] - values[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(values)):
        idx = i - 1  # gains/losses are 1 shorter
        if idx >= period:
            avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
            avg_loss = (avg_loss * (period - 1) + losses[idx]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 100.0
        result[i] = 100 - (100 / (1 + rs))
    return result


# ─── MACD ─────────────────────────────────────────────────────────────────────

def macd(
    values: List[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """Returns (macd_line, signal_line, histogram)."""
    ema_fast  = ema(values, fast)
    ema_slow  = ema(values, slow)
    macd_line = [
        (f - s) if (f is not None and s is not None) else None
        for f, s in zip(ema_fast, ema_slow)
    ]
    # Signal line = EMA of macd_line (skip Nones)
    clean_macd = [v if v is not None else 0.0 for v in macd_line]
    signal_line = ema(clean_macd, signal)
    # Restore Nones where macd_line had them
    for i, v in enumerate(macd_line):
        if v is None:
            signal_line[i] = None
    histogram = [
        (m - s) if (m is not None and s is not None) else None
        for m, s in zip(macd_line, signal_line)
    ]
    return macd_line, signal_line, histogram


# ─── Bollinger Bands ──────────────────────────────────────────────────────────

def bollinger_bands(
    values: List[float], period: int = 20, num_std: float = 2.0
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """Returns (upper, middle, lower)."""
    middle = sma(values, period)
    upper: List[Optional[float]]  = [None] * len(values)
    lower: List[Optional[float]]  = [None] * len(values)
    for i in range(period - 1, len(values)):
        window = values[i - period + 1: i + 1]
        mean = sum(window) / period
        std  = math.sqrt(sum((x - mean) ** 2 for x in window) / period)
        upper[i] = mean + num_std * std
        lower[i] = mean - num_std * std
    return upper, middle, lower


# ─── ATR ──────────────────────────────────────────────────────────────────────

def atr(
    highs: List[float], lows: List[float], closes: List[float], period: int = 14
) -> List[Optional[float]]:
    """Average True Range."""
    result: List[Optional[float]] = [None] * len(closes)
    tr_values = []
    for i in range(1, len(closes)):
        high, low, prev_close = highs[i], lows[i], closes[i - 1]
        true_range = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_values.append(true_range)
    if len(tr_values) < period:
        return result
    # First ATR = simple average
    first_atr = sum(tr_values[:period]) / period
    result[period] = first_atr
    prev_atr = first_atr
    for i in range(period + 1, len(closes)):
        current_atr = (prev_atr * (period - 1) + tr_values[i - 1]) / period
        result[i]   = current_atr
        prev_atr    = current_atr
    return result


# ─── ADX ──────────────────────────────────────────────────────────────────────

def adx(
    highs: List[float], lows: List[float], closes: List[float], period: int = 14
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """Returns (adx, plus_di, minus_di)."""
    n = len(closes)
    adx_vals:    List[Optional[float]] = [None] * n
    plus_di_v:   List[Optional[float]] = [None] * n
    minus_di_v:  List[Optional[float]] = [None] * n
    if n < period * 2:
        return adx_vals, plus_di_v, minus_di_v

    tr_list, plus_dm_list, minus_dm_list = [], [], []
    for i in range(1, n):
        hl   = highs[i] - lows[i]
        hpc  = abs(highs[i] - closes[i - 1])
        lpc  = abs(lows[i]  - closes[i - 1])
        tr_list.append(max(hl, hpc, lpc))
        up_move   = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]
        plus_dm_list.append(up_move   if up_move > down_move   and up_move   > 0 else 0.0)
        minus_dm_list.append(down_move if down_move > up_move and down_move > 0 else 0.0)

    def smooth(data: List[float], p: int) -> List[float]:
        out = [sum(data[:p])]
        for i in range(p, len(data)):
            out.append(out[-1] - out[-1] / p + data[i])
        return out

    s_tr   = smooth(tr_list, period)
    s_plus  = smooth(plus_dm_list, period)
    s_minus = smooth(minus_dm_list, period)

    dx_list = []
    for i in range(len(s_tr)):
        tr_v = s_tr[i]
        plus  = 100 * s_plus[i]  / tr_v if tr_v else 0
        minus = 100 * s_minus[i] / tr_v if tr_v else 0
        diff  = abs(plus - minus)
        total = plus + minus
        dx_list.append(100 * diff / total if total else 0)
        idx = i + period
        if idx < n:
            plus_di_v[idx]  = plus
            minus_di_v[idx] = minus

    # ADX = smoothed DX
    if len(dx_list) >= period:
        adx_seed = sum(dx_list[:period]) / period
        adx_vals[period * 2 - 1] = adx_seed
        prev = adx_seed
        for i in range(period, len(dx_list)):
            curr = (prev * (period - 1) + dx_list[i]) / period
            adx_vals[i + period] = curr
            prev = curr

    return adx_vals, plus_di_v, minus_di_v


# ─── Support & Resistance ─────────────────────────────────────────────────────

def support_resistance(
    highs: List[float], lows: List[float], window: int = 10
) -> Tuple[List[float], List[float]]:
    """Detect local pivot highs and lows."""
    supports: List[float] = []
    resistances: List[float] = []
    for i in range(window, len(highs) - window):
        # Resistance pivot
        if highs[i] == max(highs[i - window: i + window + 1]):
            resistances.append(highs[i])
        # Support pivot
        if lows[i] == min(lows[i - window: i + window + 1]):
            supports.append(lows[i])
    return sorted(supports[-5:]), sorted(resistances[-5:], reverse=True)[:5]


# ─── Volume Analysis ──────────────────────────────────────────────────────────

def relative_volume(volumes: List[float], period: int = 20) -> Optional[float]:
    """Current volume relative to average. >1.5 = high volume."""
    if len(volumes) < period + 1:
        return None
    avg = sum(volumes[-period - 1: -1]) / period
    return volumes[-1] / avg if avg else None
