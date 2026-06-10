"""
Halol Crypto AI - Utilities
Message formatting, keyboard builders, number formatters.
"""

import logging
from typing import List, Optional, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)


# ─── Number Formatters ────────────────────────────────────────────────────────

def fmt_price(price: float) -> str:
    """Format price with appropriate precision."""
    if price == 0:
        return "N/A"
    if price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:.4f}"
    elif price >= 0.01:
        return f"${price:.6f}"
    else:
        return f"${price:.8f}"


def fmt_change(change: float) -> str:
    """Format 24h change with emoji."""
    if change > 0:
        return f"🟢 +{change:.2f}%"
    elif change < 0:
        return f"🔴 {change:.2f}%"
    else:
        return f"⚪ 0.00%"


def fmt_volume(volume: float) -> str:
    """Format large volume numbers."""
    if volume >= 1_000_000_000:
        return f"${volume / 1_000_000_000:.2f}B"
    elif volume >= 1_000_000:
        return f"${volume / 1_000_000:.2f}M"
    elif volume >= 1_000:
        return f"${volume / 1_000:.1f}K"
    return f"${volume:.2f}"


def fmt_pct(value: float) -> str:
    return f"{value:.1f}%"


# ─── Keyboard Builders ────────────────────────────────────────────────────────

def back_home_row() -> List[InlineKeyboardButton]:
    """Standard back/home navigation row."""
    return [
        InlineKeyboardButton("◀️ Back", callback_data="back"),
        InlineKeyboardButton("🏠 Home", callback_data="home"),
    ]


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Signals",          callback_data="menu_signals"),
         InlineKeyboardButton("🔥 Top Opportunities", callback_data="menu_top")],
        [InlineKeyboardButton("⭐ Watchlist",         callback_data="menu_watchlist"),
         InlineKeyboardButton("📊 Market Overview",   callback_data="menu_market")],
        [InlineKeyboardButton("🎓 Academy",           callback_data="menu_academy"),
         InlineKeyboardButton("🤖 AI Helper",         callback_data="menu_ai")],
        [InlineKeyboardButton("⚙️ Settings",          callback_data="menu_settings")],
    ])


def coin_list_keyboard(
    coins: List[dict],
    page: int = 0,
    per_page: int = 8,
    callback_prefix: str = "signal_coin",
) -> InlineKeyboardMarkup:
    """Paginated coin selection keyboard."""
    start = page * per_page
    end   = start + per_page
    page_coins = coins[start:end]
    total_pages = (len(coins) + per_page - 1) // per_page

    rows = []
    # 2 coins per row
    for i in range(0, len(page_coins), 2):
        row = []
        for coin in page_coins[i: i + 2]:
            sym = coin["symbol"]
            row.append(InlineKeyboardButton(
                f"{sym}", callback_data=f"{callback_prefix}:{sym}"
            ))
        rows.append(row)

    # Pagination
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"coinpage:{callback_prefix}:{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"coinpage:{callback_prefix}:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append(back_home_row())
    return InlineKeyboardMarkup(rows)


def timeframe_keyboard(symbol: str, back_cb: str = "menu_signals") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("15m", callback_data=f"tf:{symbol}:15m"),
            InlineKeyboardButton("1H",  callback_data=f"tf:{symbol}:1h"),
            InlineKeyboardButton("4H",  callback_data=f"tf:{symbol}:4h"),
            InlineKeyboardButton("1D",  callback_data=f"tf:{symbol}:1d"),
        ],
        [InlineKeyboardButton("◀️ Back", callback_data=back_cb),
         InlineKeyboardButton("🏠 Home", callback_data="home")],
    ])


def signal_detail_keyboard(symbol: str, in_watchlist: bool = False) -> InlineKeyboardMarkup:
    wl_btn = (
        InlineKeyboardButton("⭐ Remove from Watchlist", callback_data=f"wl_remove:{symbol}")
        if in_watchlist else
        InlineKeyboardButton("⭐ Add to Watchlist",      callback_data=f"wl_add:{symbol}")
    )
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh Signal", callback_data=f"refresh_signal:{symbol}")],
        [wl_btn],
        [InlineKeyboardButton("📊 Change Timeframe", callback_data=f"change_tf:{symbol}")],
        back_home_row(),
    ])


def academy_keyboard() -> InlineKeyboardMarkup:
    from education import CATEGORIES
    rows = []
    cats = list(CATEGORIES.items())
    for i in range(0, len(cats), 2):
        row = []
        for key, label in cats[i: i + 2]:
            row.append(InlineKeyboardButton(label, callback_data=f"academy_cat:{key}"))
        rows.append(row)
    rows.append(back_home_row())
    return InlineKeyboardMarkup(rows)


def lesson_list_keyboard(category: str, lessons: List[dict]) -> InlineKeyboardMarkup:
    rows = []
    for lesson in lessons:
        rows.append([InlineKeyboardButton(
            f"{lesson.get('emoji', '📖')} {lesson['title']}",
            callback_data=f"lesson:{lesson['key']}"
        )])
    rows.append([
        InlineKeyboardButton("◀️ Back", callback_data="menu_academy"),
        InlineKeyboardButton("🏠 Home", callback_data="home"),
    ])
    return InlineKeyboardMarkup(rows)


def watchlist_keyboard(symbols: List[str]) -> InlineKeyboardMarkup:
    rows = []
    for sym in symbols:
        rows.append([
            InlineKeyboardButton(f"📈 {sym}", callback_data=f"signal_coin:{sym}"),
            InlineKeyboardButton(f"❌ Remove", callback_data=f"wl_remove:{sym}"),
        ])
    rows.append([InlineKeyboardButton("➕ Add Coin", callback_data="wl_browse")])
    rows.append(back_home_row())
    return InlineKeyboardMarkup(rows)


def settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    tf = settings.get("default_tf", "4h")
    alerts = "🔔 ON" if settings.get("alert_enabled") else "🔕 OFF"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⏱ Default Timeframe: {tf.upper()}",
                              callback_data="settings_tf")],
        [InlineKeyboardButton(f"Alerts: {alerts}",
                              callback_data="settings_alerts")],
        back_home_row(),
    ])


def settings_tf_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("15m", callback_data="set_tf:15m"),
            InlineKeyboardButton("1H",  callback_data="set_tf:1h"),
            InlineKeyboardButton("4H",  callback_data="set_tf:4h"),
            InlineKeyboardButton("1D",  callback_data="set_tf:1d"),
        ],
        back_home_row(),
    ])


# ─── Message Formatters ───────────────────────────────────────────────────────

def format_signal_message(result) -> str:
    """Format a full signal result for Telegram."""
    tp  = result.trade_plan
    smc = result.smc
    ind = result.indicators

    rsi_v   = ind.get("rsi")
    macd_v  = ind.get("macd_line")
    adx_v   = ind.get("adx")
    rv      = ind.get("relative_volume")
    e20     = ind.get("ema20")
    e50     = ind.get("ema50")
    e200    = ind.get("ema200")

    smc_badges = ""
    if smc:
        if smc.bos_detected:     smc_badges += "💥 BOS  "
        if smc.choch_detected:   smc_badges += "🔄 CHoCH  "
        if smc.liquidity_sweep:  smc_badges += "🌊 Liq Sweep  "
        if smc.breakout_retest:  smc_badges += "🚀 Retest  "
        if smc.order_blocks:     smc_badges += f"🏦 {len(smc.order_blocks)} OB  "
        if smc.fair_value_gaps:  smc_badges += f"⚡ {len(smc.fair_value_gaps)} FVG  "

    msg = (
        f"<b>{result.signal_type} — {result.symbol}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💹 Price: <b>{fmt_price(result.price)}</b>  "
        f"{fmt_change(result.change_24h)}\n"
        f"⏱ Timeframe: <b>{result.timeframe.upper()}</b>\n\n"
        f"📊 Signal Score: <b>{result.score:.0f}/100</b>\n"
        f"🎯 Confidence: <b>{result.confidence:.0f}%</b>\n"
        f"📈 Trend: <b>{result.trend}</b>\n"
        f"⚡ Momentum: <b>{result.momentum}</b>\n"
        f"⚠️ Risk: <b>{result.risk}</b>\n\n"
    )

    # Trade Plan
    if tp.entry > 0:
        msg += (
            f"📋 <b>Trade Plan</b>\n"
            f"┣ Entry:  {fmt_price(tp.entry)}\n"
            f"┣ 🛑 Stop:  {fmt_price(tp.stop_loss)}\n"
            f"┣ 🎯 TP1:   {fmt_price(tp.take_profit1)}\n"
            f"┣ 🎯 TP2:   {fmt_price(tp.take_profit2)}\n"
            f"┣ 🎯 TP3:   {fmt_price(tp.take_profit3)}\n"
            f"┗ ⚖️ R/R:   1:{tp.risk_reward}\n\n"
        )

    # Indicators
    ind_lines = []
    if rsi_v:   ind_lines.append(f"RSI: {rsi_v:.1f}")
    if macd_v:  ind_lines.append(f"MACD: {'▲' if macd_v > 0 else '▼'}{abs(macd_v):.4f}")
    if adx_v:   ind_lines.append(f"ADX: {adx_v:.1f}")
    if rv:      ind_lines.append(f"RelVol: {rv:.2f}x")
    if e20:     ind_lines.append(f"EMA20: {fmt_price(e20)}")
    if e200:    ind_lines.append(f"EMA200: {fmt_price(e200)}")

    if ind_lines:
        msg += f"📊 <b>Indicators</b>\n{' | '.join(ind_lines)}\n\n"

    # SMC
    if smc_badges:
        msg += f"🏦 <b>Smart Money</b>\n{smc_badges.strip()}\n"
        if smc:
            msg += f"Structure: {smc.market_structure}\n"

    msg += "\n⚠️ <i>Not financial advice. Always DYOR.</i>"
    return msg


def format_coin_card(symbol: str, name: str, price: float, change: float) -> str:
    arrow = "🟢" if change >= 0 else "🔴"
    return (
        f"{arrow} <b>{symbol}</b> ({name})\n"
        f"   {fmt_price(price)}  {fmt_change(change)}"
    )


def format_market_overview(coins: List[dict], sentiment: dict) -> str:
    msg = (
        f"📊 <b>Market Overview</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 Sentiment: <b>{sentiment.get('sentiment', 'N/A')}</b>\n"
        f"₿ BTC Dominance: <b>{sentiment.get('btc_dominance', 'N/A')}%</b>\n"
        f"📈 Market 24h: <b>{fmt_change(sentiment.get('total_change_24h', 0))}</b>\n\n"
    )

    # Sort by change
    sorted_coins = sorted(coins, key=lambda c: c.get("change_24h", 0), reverse=True)

    gainers = sorted_coins[:5]
    losers  = sorted_coins[-3:][::-1]

    msg += "🔥 <b>Top Gainers</b>\n"
    for c in gainers:
        if c.get("price"):
            msg += f"  {format_coin_card(c['symbol'], c['name'], c['price'], c['change_24h'])}\n"

    msg += "\n📉 <b>Watch Out</b>\n"
    for c in losers:
        if c.get("price"):
            msg += f"  {format_coin_card(c['symbol'], c['name'], c['price'], c['change_24h'])}\n"

    return msg
