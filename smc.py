"""
Halol Crypto AI - Smart Money Concepts (SMC)
Detects institutional patterns: Order Blocks, FVG, BOS, CHoCH, etc.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SMCResult:
    order_blocks:     List[Dict] = field(default_factory=list)
    fair_value_gaps:  List[Dict] = field(default_factory=list)
    bos_detected:     bool = False
    choch_detected:   bool = False
    liquidity_sweep:  bool = False
    breakout_retest:  bool = False
    market_structure: str = "Neutral"   # Bullish / Bearish / Neutral
    premium_zone:     Optional[float] = None
    discount_zone:    Optional[float] = None
    equilibrium:      Optional[float] = None
    smc_score:        float = 0.0       # 0-100 contribution to signal


# ─── Order Blocks ─────────────────────────────────────────────────────────────

def detect_order_blocks(
    opens: List[float],
    highs: List[float],
    lows: List[float],
    closes: List[float],
    lookback: int = 30,
) -> List[Dict]:
    """
    Bullish Order Block: last down-close candle before a strong up-move.
    Bearish Order Block: last up-close candle before a strong down-move.
    Returns last 3 blocks for context.
    """
    blocks = []
    n = len(closes)
    if n < 5:
        return blocks

    start = max(0, n - lookback)
    for i in range(start, n - 3):
        body_i = abs(closes[i] - opens[i])

        # Bullish OB: bearish candle (close < open) followed by 2+ bullish candles
        if closes[i] < opens[i]:
            follow_up = all(closes[i + j] > opens[i + j] for j in range(1, 3))
            if follow_up:
                total_move = closes[i + 2] - closes[i]
                if total_move > body_i * 1.5:
                    blocks.append({
                        "type": "Bullish OB",
                        "high": highs[i],
                        "low":  lows[i],
                        "mid":  (highs[i] + lows[i]) / 2,
                        "index": i,
                        "strength": min(100, int(total_move / closes[i] * 1000)),
                    })

        # Bearish OB: bullish candle followed by 2+ bearish
        elif closes[i] > opens[i]:
            follow_down = all(closes[i + j] < opens[i + j] for j in range(1, 3))
            if follow_down:
                total_move = closes[i] - closes[i + 2]
                if total_move > body_i * 1.5:
                    blocks.append({
                        "type": "Bearish OB",
                        "high": highs[i],
                        "low":  lows[i],
                        "mid":  (highs[i] + lows[i]) / 2,
                        "index": i,
                        "strength": min(100, int(total_move / closes[i] * 1000)),
                    })

    # Return most recent 3
    return blocks[-3:] if blocks else []


# ─── Fair Value Gaps ──────────────────────────────────────────────────────────

def detect_fvg(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    lookback: int = 40,
) -> List[Dict]:
    """
    Bullish FVG: gap between candle[i-1].high and candle[i+1].low when candle[i] is bullish.
    Bearish FVG: gap between candle[i-1].low and candle[i+1].high when candle[i] is bearish.
    """
    gaps = []
    n = len(closes)
    if n < 3:
        return gaps

    start = max(1, n - lookback)
    for i in range(start, n - 1):
        # Bullish FVG
        gap_top    = lows[i + 1]
        gap_bottom = highs[i - 1]
        if gap_top > gap_bottom:
            gap_size = (gap_top - gap_bottom) / closes[i] * 100
            if gap_size > 0.1:  # At least 0.1% gap
                gaps.append({
                    "type":   "Bullish FVG",
                    "top":    gap_top,
                    "bottom": gap_bottom,
                    "mid":    (gap_top + gap_bottom) / 2,
                    "size_pct": round(gap_size, 3),
                    "filled": False,
                    "index":  i,
                })

        # Bearish FVG
        gap_top2    = lows[i - 1]
        gap_bottom2 = highs[i + 1]
        if gap_top2 > gap_bottom2:
            gap_size2 = (gap_top2 - gap_bottom2) / closes[i] * 100
            if gap_size2 > 0.1:
                gaps.append({
                    "type":   "Bearish FVG",
                    "top":    gap_top2,
                    "bottom": gap_bottom2,
                    "mid":    (gap_top2 + gap_bottom2) / 2,
                    "size_pct": round(gap_size2, 3),
                    "filled": False,
                    "index":  i,
                })

    return gaps[-4:] if gaps else []


# ─── Break of Structure ───────────────────────────────────────────────────────

def detect_bos(
    highs: List[float],
    lows: List[float],
    closes: List[float],
) -> Tuple[bool, bool]:
    """
    BOS Bullish: current close breaks above the last swing high.
    BOS Bearish: current close breaks below the last swing low.
    Returns (bos_bullish, bos_bearish).
    """
    if len(closes) < 20:
        return False, False

    last_swing_high = max(highs[-20:-2])
    last_swing_low  = min(lows[-20:-2])
    current_close   = closes[-1]

    bos_bullish = current_close > last_swing_high
    bos_bearish = current_close < last_swing_low
    return bos_bullish, bos_bearish


# ─── Change of Character ──────────────────────────────────────────────────────

def detect_choch(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    lookback: int = 50,
) -> bool:
    """
    CHoCH: structure was bearish (lower highs, lower lows), then suddenly
    makes a higher high — or vice versa.
    """
    if len(closes) < lookback:
        return False

    h = highs[-lookback:]
    l = lows[-lookback:]

    # Check for recent lower-high sequence then break up
    mid = lookback // 2
    prev_high = max(h[:mid])
    recent_high = max(h[mid:])
    prev_low    = min(l[:mid])
    recent_low  = min(l[mid:])

    # Bearish→Bullish CHoCH
    bearish_to_bullish = (
        prev_high > max(h[mid // 2: mid]) and   # was making lower highs
        recent_high > prev_high                   # then broke above
    )
    # Bullish→Bearish CHoCH
    bullish_to_bearish = (
        prev_low < min(l[mid // 2: mid]) and
        recent_low < prev_low
    )
    return bearish_to_bullish or bullish_to_bearish


# ─── Liquidity Sweep ──────────────────────────────────────────────────────────

def detect_liquidity_sweep(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    lookback: int = 30,
) -> bool:
    """
    Wick pierces a key level but closes back inside — classic liquidity grab.
    """
    if len(closes) < lookback + 2:
        return False

    key_high = max(highs[-lookback - 1:-2])
    key_low  = min(lows[-lookback - 1:-2])
    last_high  = highs[-1]
    last_low   = lows[-1]
    last_close = closes[-1]

    # Price wicked above key_high but closed below it
    swept_high = last_high > key_high and last_close < key_high
    # Price wicked below key_low but closed above it
    swept_low  = last_low < key_low  and last_close > key_low

    return swept_high or swept_low


# ─── Breakout Retest ──────────────────────────────────────────────────────────

def detect_breakout_retest(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    lookback: int = 20,
) -> bool:
    """
    Price broke above resistance, then pulled back to test it as support.
    """
    if len(closes) < lookback + 5:
        return False

    resistance = max(highs[-lookback - 5:-5])
    recent_closes = closes[-5:]
    broken = any(c > resistance for c in closes[-lookback:-5])
    retesting = any(abs(c - resistance) / resistance < 0.015 for c in recent_closes)
    return broken and retesting


# ─── Premium / Discount Zones ─────────────────────────────────────────────────

def premium_discount_zones(
    highs: List[float],
    lows: List[float],
    lookback: int = 50,
) -> Dict[str, float]:
    """
    Equilibrium = midpoint of the range.
    Premium = upper half. Discount = lower half.
    """
    if len(highs) < lookback:
        lookback = len(highs)
    high = max(highs[-lookback:])
    low  = min(lows[-lookback:])
    mid  = (high + low) / 2
    return {
        "high":        high,
        "low":         low,
        "equilibrium": mid,
        "premium":     (high + mid) / 2,
        "discount":    (low + mid) / 2,
    }


# ─── Master SMC Analyzer ──────────────────────────────────────────────────────

def analyze_smc(
    opens:  List[float],
    highs:  List[float],
    lows:   List[float],
    closes: List[float],
) -> SMCResult:
    """Run all SMC detections and return a combined SMCResult."""
    result = SMCResult()

    try:
        result.order_blocks    = detect_order_blocks(opens, highs, lows, closes)
        result.fair_value_gaps = detect_fvg(highs, lows, closes)

        bos_bull, bos_bear     = _bos(highs, lows, closes)
        result.bos_detected    = bos_bull or bos_bear
        result.choch_detected  = detect_choch(highs, lows, closes)
        result.liquidity_sweep = detect_liquidity_sweep(highs, lows, closes)
        result.breakout_retest = detect_breakout_retest(highs, lows, closes)

        zones = premium_discount_zones(highs, lows)
        result.premium_zone   = zones["premium"]
        result.discount_zone  = zones["discount"]
        result.equilibrium    = zones["equilibrium"]

        current = closes[-1]
        if current < zones["discount"]:
            result.market_structure = "Discount (Bullish)"
        elif current > zones["premium"]:
            result.market_structure = "Premium (Caution)"
        else:
            result.market_structure = "Equilibrium"

        # Score
        score = 0.0
        bullish_obs = [ob for ob in result.order_blocks if ob["type"] == "Bullish OB"]
        if bullish_obs:
            score += 20
        if result.bos_detected:
            score += 15
        if result.choch_detected:
            score += 10
        if result.liquidity_sweep:
            score += 15
        if result.breakout_retest:
            score += 20
        bullish_fvgs = [g for g in result.fair_value_gaps if g["type"] == "Bullish FVG"]
        if bullish_fvgs:
            score += 15
        if "Discount" in result.market_structure:
            score += 5
        result.smc_score = min(score, 100.0)

    except Exception as e:
        logger.warning("SMC analysis error: %s", e)

    return result


def _bos(highs, lows, closes):
    """Internal BOS helper (avoids the stub above)."""
    if len(closes) < 20:
        return False, False
    last_swing_high = max(highs[-20:-2])
    last_swing_low  = min(lows[-20:-2])
    current_close   = closes[-1]
    return current_close > last_swing_high, current_close < last_swing_low
