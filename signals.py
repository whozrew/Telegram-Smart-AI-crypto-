"""
Halol Crypto AI - Signal Engine
Combines all indicators + SMC into a 0-100 score with trade plan.
HALAL ONLY: No short signals, no leverage, no futures.
"""

import logging
import math
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from indicators import (
    ema, rsi, macd, bollinger_bands, atr, adx,
    support_resistance, relative_volume,
)
from smc import analyze_smc, SMCResult

logger = logging.getLogger(__name__)


# ─── Signal Types (Halal — no Short/Sell) ────────────────────────────────────

SIGNAL_STRONG_BUY = "🟢 Strong Buy"
SIGNAL_BUY        = "🟢 Buy"
SIGNAL_WAIT       = "🟡 Wait"
SIGNAL_PROFIT     = "💰 Profit Taking Zone"


@dataclass
class TradePlan:
    entry:       float = 0.0
    stop_loss:   float = 0.0
    take_profit1: float = 0.0
    take_profit2: float = 0.0
    take_profit3: float = 0.0
    risk_reward: float = 0.0


@dataclass
class SignalResult:
    symbol:       str = ""
    timeframe:    str = ""
    signal_type:  str = SIGNAL_WAIT
    score:        float = 0.0       # 0-100
    confidence:   float = 0.0       # 0-100
    trend:        str = "Neutral"
    momentum:     str = "Neutral"
    risk:         str = "Medium"
    trade_plan:   TradePlan = field(default_factory=TradePlan)
    smc:          Optional[SMCResult] = None
    indicators:   Dict[str, Any] = field(default_factory=dict)
    price:        float = 0.0
    change_24h:   float = 0.0
    error:        Optional[str] = None


# ─── Scoring Components ───────────────────────────────────────────────────────

def _score_ema(closes: List[float], price: float) -> tuple:
    """EMA alignment score. Bull: price > EMA20 > EMA50 > EMA200."""
    e20  = ema(closes, 20)
    e50  = ema(closes, 50)
    e200 = ema(closes, 200)
    v20  = next((v for v in reversed(e20)  if v is not None), None)
    v50  = next((v for v in reversed(e50)  if v is not None), None)
    v200 = next((v for v in reversed(e200) if v is not None), None)
    if None in (v20, v50, v200):
        return 0.0, {}
    score = 0.0
    if price > v20:  score += 8
    if price > v50:  score += 8
    if price > v200: score += 9
    if v20  > v50:   score += 5
    if v50  > v200:  score += 5
    return score, {"ema20": v20, "ema50": v50, "ema200": v200}


def _score_rsi(closes: List[float]) -> tuple:
    """RSI score. Buy zone: 40-65."""
    vals = rsi(closes, 14)
    v = next((x for x in reversed(vals) if x is not None), None)
    if v is None:
        return 0.0, None
    score = 0.0
    if 40 <= v <= 65:   score = 15
    elif 30 <= v < 40:  score = 10  # Oversold recovery
    elif 65 < v <= 70:  score = 8   # Getting hot
    elif v < 30:        score = 5   # Very oversold — risky entry
    return score, v


def _score_macd(closes: List[float]) -> tuple:
    """MACD score. Bullish crossover = high score."""
    ml, sl, hist = macd(closes)
    v_ml   = next((x for x in reversed(ml)   if x is not None), None)
    v_sl   = next((x for x in reversed(sl)   if x is not None), None)
    v_hist = next((x for x in reversed(hist) if x is not None), None)
    if None in (v_ml, v_sl, v_hist):
        return 0.0, {}
    score = 0.0
    if v_ml > 0:     score += 5
    if v_ml > v_sl:  score += 8
    if v_hist > 0:
        # Recent histogram expansion = momentum
        prev_hist = [x for x in hist[-10:] if x is not None]
        if len(prev_hist) >= 2 and prev_hist[-1] > prev_hist[-2]:
            score += 7
    return score, {"macd_line": v_ml, "signal": v_sl, "histogram": v_hist}


def _score_bb(closes: List[float], price: float) -> tuple:
    """Bollinger Bands — near lower band = buy opportunity."""
    upper, middle, lower = bollinger_bands(closes, 20, 2.0)
    v_u = next((x for x in reversed(upper)  if x is not None), None)
    v_m = next((x for x in reversed(middle) if x is not None), None)
    v_l = next((x for x in reversed(lower)  if x is not None), None)
    if None in (v_u, v_m, v_l):
        return 0.0, {}
    band_width = (v_u - v_l) / v_m * 100 if v_m else 0
    score = 0.0
    pct_b = (price - v_l) / (v_u - v_l) if (v_u - v_l) else 0.5
    if pct_b < 0.3:   score = 10  # Near lower band = buy zone
    elif pct_b < 0.5: score = 8
    elif pct_b < 0.7: score = 5
    else:             score = 2   # Near upper band = watch
    return score, {"upper": v_u, "middle": v_m, "lower": v_l, "pct_b": round(pct_b, 2)}


def _score_adx_trend(highs, lows, closes) -> tuple:
    """ADX — strength of trend. High ADX with +DI > -DI = strong bull."""
    adx_v, plus_di, minus_di = adx(highs, lows, closes)
    v_adx  = next((x for x in reversed(adx_v)   if x is not None), None)
    v_plus = next((x for x in reversed(plus_di)  if x is not None), None)
    v_min  = next((x for x in reversed(minus_di) if x is not None), None)
    if None in (v_adx, v_plus, v_min):
        return 0.0, {}
    score = 0.0
    if v_adx > 25 and v_plus > v_min:
        score = 10
    elif v_adx > 20 and v_plus > v_min:
        score = 7
    elif v_adx < 20:
        score = 3  # Ranging, less reliable
    trend = "Strong Bull" if v_adx > 25 and v_plus > v_min else \
            "Bull"        if v_plus > v_min else \
            "Bear"        if v_min  > v_plus else "Neutral"
    return score, {"adx": v_adx, "plus_di": v_plus, "minus_di": v_min, "trend": trend}


def _score_volume(volumes: List[float]) -> tuple:
    """Volume relative to average."""
    rv = relative_volume(volumes, 20)
    if rv is None:
        return 0.0, None
    if rv >= 2.0:   score = 10
    elif rv >= 1.5: score = 7
    elif rv >= 1.0: score = 4
    else:           score = 1
    return score, round(rv, 2)


# ─── Trade Plan Calculator ────────────────────────────────────────────────────

def _calculate_trade_plan(
    price: float,
    atr_val: Optional[float],
    supports: List[float],
    resistances: List[float],
) -> TradePlan:
    """Generate entry, SL, TP1/2/3 based on ATR and S/R levels."""
    if atr_val is None or atr_val == 0:
        atr_val = price * 0.015  # Fallback: 1.5% of price

    entry = price
    stop_loss = max(price - atr_val * 1.5, price * 0.93)
    if supports:
        nearest_support = max([s for s in supports if s < price], default=stop_loss)
        stop_loss = min(stop_loss, nearest_support * 0.99)

    risk = entry - stop_loss
    tp1 = entry + risk * 1.5
    tp2 = entry + risk * 2.5
    tp3 = entry + risk * 4.0

    # Override with resistance if available
    if resistances:
        above_res = [r for r in resistances if r > entry]
        if len(above_res) >= 1: tp1 = above_res[0] * 0.99
        if len(above_res) >= 2: tp2 = above_res[1] * 0.99
        if len(above_res) >= 3: tp3 = above_res[2] * 0.99

    rr = (tp1 - entry) / risk if risk > 0 else 0

    return TradePlan(
        entry=round(entry, 6),
        stop_loss=round(stop_loss, 6),
        take_profit1=round(tp1, 6),
        take_profit2=round(tp2, 6),
        take_profit3=round(tp3, 6),
        risk_reward=round(rr, 2),
    )


# ─── Main Signal Analyzer ─────────────────────────────────────────────────────

def analyze_signal(
    symbol:    str,
    timeframe: str,
    candles:   List[Dict],   # [{open, high, low, close, volume}, ...]
    price:     float = 0.0,
    change_24h: float = 0.0,
) -> SignalResult:
    """
    Full signal analysis pipeline.
    Returns SignalResult with score, signal type, and trade plan.
    """
    result = SignalResult(symbol=symbol, timeframe=timeframe)
    result.price     = price
    result.change_24h = change_24h

    if len(candles) < 50:
        result.error = "Insufficient data (need 50+ candles)"
        result.signal_type = SIGNAL_WAIT
        return result

    try:
        opens   = [c["open"]   for c in candles]
        highs   = [c["high"]   for c in candles]
        lows    = [c["low"]    for c in candles]
        closes  = [c["close"]  for c in candles]
        volumes = [c["volume"] for c in candles]
        last_close = closes[-1]

        total_score = 0.0
        indicators  = {}

        # EMA
        ema_score, ema_vals = _score_ema(closes, last_close)
        total_score += ema_score
        indicators.update(ema_vals or {})

        # RSI
        rsi_score, rsi_val = _score_rsi(closes)
        total_score += rsi_score
        indicators["rsi"] = rsi_val

        # MACD
        macd_score, macd_vals = _score_macd(closes)
        total_score += macd_score
        indicators.update(macd_vals or {})

        # Bollinger
        bb_score, bb_vals = _score_bb(closes, last_close)
        total_score += bb_score
        indicators.update(bb_vals or {})

        # ADX/Trend
        adx_score, adx_vals = _score_adx_trend(highs, lows, closes)
        total_score += adx_score
        indicators.update(adx_vals or {})
        trend_label = adx_vals.get("trend", "Neutral") if adx_vals else "Neutral"

        # Volume
        vol_score, rv = _score_volume(volumes)
        total_score += vol_score
        indicators["relative_volume"] = rv

        # ATR
        atr_vals = atr(highs, lows, closes)
        atr_val  = next((x for x in reversed(atr_vals) if x is not None), None)
        indicators["atr"] = atr_val

        # Support / Resistance
        supports, resistances = support_resistance(highs, lows)
        indicators["supports"]    = supports
        indicators["resistances"] = resistances

        # SMC Analysis
        smc_result = analyze_smc(opens, highs, lows, closes)
        smc_contrib = smc_result.smc_score * 0.25  # 25% weight
        total_score += smc_contrib
        result.smc = smc_result

        # Normalize to 0-100
        max_possible = 35 + 15 + 20 + 10 + 10 + 10 + 25  # EMA+RSI+MACD+BB+ADX+VOL+SMC
        score = min(100.0, (total_score / max_possible) * 100)
        result.score = round(score, 1)
        result.indicators = indicators

        # Signal classification
        if score >= 75:
            result.signal_type = SIGNAL_STRONG_BUY
            result.risk = "Low-Medium"
        elif score >= 55:
            result.signal_type = SIGNAL_BUY
            result.risk = "Medium"
        elif score >= 40:
            result.signal_type = SIGNAL_WAIT
            result.risk = "Medium-High"
        else:
            result.signal_type = SIGNAL_PROFIT
            result.risk = "High"

        result.confidence = round(score, 1)
        result.trend      = trend_label

        # Momentum
        if rsi_val and rsi_val > 55:
            result.momentum = "Strong"
        elif rsi_val and rsi_val > 45:
            result.momentum = "Moderate"
        else:
            result.momentum = "Weak"

        # Trade plan
        result.trade_plan = _calculate_trade_plan(
            price=last_close,
            atr_val=atr_val,
            supports=supports,
            resistances=resistances,
        )

    except Exception as e:
        logger.exception("Signal analysis failed for %s: %s", symbol, e)
        result.error = str(e)

    return result


# ─── Helpers ──────────────────────────────────────────────────────────────────

def format_signal_emoji(signal_type: str) -> str:
    mapping = {
        SIGNAL_STRONG_BUY: "🟢",
        SIGNAL_BUY:        "🟢",
        SIGNAL_WAIT:       "🟡",
        SIGNAL_PROFIT:     "💰",
    }
    return mapping.get(signal_type, "⚪")
