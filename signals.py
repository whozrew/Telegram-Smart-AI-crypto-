from typing import Dict, Any
import pandas as pd

def generate_trading_signal(df_dict: Dict[str, pd.DataFrame], coin: str) -> Dict[str, Any]:
    """Ko'p vaqtli tahlil (Multi-timeframe) va SMC asosida yakuniy halol signal tayyorlash"""
    df_1h = df_dict.get('1h')
    df_4h = df_dict.get('4h')
    
    if df_1h is None or df_4h is None or len(df_1h) < 20:
        return {"signal": "🟡 KUTISH", "score": 50, "rationale": "Ma'lumot yetarli emas."}

    from utils import detect_smc_and_advanced
    smc_1h = detect_smc_and_advanced(df_1h)
    
    last_1h = df_1h.iloc[-1]
    last_4h = df_4h.iloc[-1]
    
    # 1. Skoring Tizimi poydevori
    score = 50
    reasons = []

    # Trend va Momentum tahlili (4H ustuvorlik vazni yuqori)
    if last_4h['close'] > last_4h['EMA50']:
        score += 15
        reasons.append("4H trend yuqoriga (Bullish)")
    else:
        score -= 15
        reasons.append("4H trend pastga (Bearish)")

    if last_1h['RSI'] > 50 and last_1h['RSI'] < 70:
        score += 10
        reasons.append("RSI sog'lom yuksalish zonasida")
    elif last_1h['RSI'] > 70:
        score -= 5
        reasons.append("RSI haddan tashqari sotib olingan")

    if last_1h['MACD'] > last_1h['MACD_Signal']:
        score += 10
        reasons.append("MACD Bullish kesishish mavjud")

    # SMC va Murakkab Price Action elementlari tasdig'i
    if smc_1h["bos"] or smc_1h["choch"]:
        score += 15
        reasons.append("Bozor strukturasi buzib o'tildi (BOS/CHoCH)")
    if smc_1h["fvg_bullish"]:
        score += 10
        reasons.append("Bullish Imbalance (FVG) aniqlandi")
    if smc_1h["order_block_bullish"]:
        score += 15
        reasons.append("Yirik xaridorlar bloki (Bullish Order Block) shakllandi")
    if smc_1h["liquidity_sweep_bullish"]:
        score += 15
        reasons.append("Likvidlik yig'ib olindi (Bullish Sweep)")
    if smc_1h["breakout_retest"]:
        score += 20
        reasons.append("Qarshilik darajasi muvaffaqiyatli retest qilindi")

    # Hajm (RVOL) filtri va risk boshqaruvi tuzatishlari
    rvol = smc_1h["rvol"]
    if rvol > 2.0:
        score += 10
        reasons.append("Savdo hajmi keskin oshgan (RVOL > 2.0)")
    elif rvol < 0.8:
        score -= 15
        reasons.append("Bozor qiziqishi sust, hajm yetarsiz")

    # Risk cheklovlari (Bearish sharoitlar xavfni oshiradi)
    if smc_1h["fvg_bearish"] or smc_1h["order_block_bearish"] or smc_1h["liquidity_sweep_bearish"]:
        score -= 20
        reasons.append("Bearish Price Action belgilari bor, xavf yuqori")

    # Ball chegaralari
    score = max(0, min(100, score))

    # Signal statusini aniqlash
    if score >= 80:
        signal_type = "🔥 KUCHLI SOTIB OLISH"
    elif score >= 60:
        signal_type = "🟢 SOTIB OLISH"
    elif score >= 40:
        signal_type = "🟡 KUTISH"
    elif score >= 25:
        signal_type = "🔵 FOYDA OLISH"
    else:
        signal_type = "🟠 XAVF OSHDI"

    # Risk Management parametrlari (Faqat Spot uchun matematik hisoblar)
    current_price = float(last_1h['close'])
    atr = float(last_1h['ATR']) if not pd.isna(last_1h['ATR']) else current_price * 0.02
    
    stop_loss = current_price - (atr * 2)
    tp1 = current_price + (atr * 2)
    tp2 = current_price + (atr * 4)
    tp3 = current_price + (atr * 6)
    
    risk_reward = round((tp2 - current_price) / (current_price - stop_loss + 1e-10), 1)
    entry_quality = int(score * 0.95 + (10 if smc_1h["breakout_retest"] else 0))
    entry_quality = min(100, max(0, entry_quality))

    rationale_text = "Nega signal berildi:\n" + "\n".join([f"• {r}" for r in reasons])

    return {
        "signal": signal_type,
        "score": score,
        "price": current_price,
        "stop_loss": round(stop_loss, 4),
        "tp1": round(tp1, 4),
        "tp2": round(tp2, 4),
        "tp3": round(tp3, 4),
        "risk_reward": f"1:{risk_reward}",
        "entry_quality": entry_quality,
        "rationale": rationale_text
    }
