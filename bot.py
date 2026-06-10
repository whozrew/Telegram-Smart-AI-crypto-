"""
Halol Crypto AI - Telegram Bot
Full button-driven UX. No manual coin typing required.
"""

import asyncio
import logging
import os
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
from telegram.constants import ParseMode

from config import BOT_TOKEN, WEBAPP_URL, HALAL_COINS, TIMEFRAMES
from database import (
    init_db, upsert_user, get_watchlist, add_to_watchlist,
    remove_from_watchlist, get_user_settings, update_user_settings,
    get_active_alerts,
)
from scanner import (
    fetch_candles, fetch_ticker_24h, fetch_market_overview,
    fetch_global_sentiment, fetch_watchlist_data,
)
from signals import analyze_signal
from education import (
    get_all_categories, get_lessons_by_category, get_lesson, CATEGORIES,
)
from utils import (
    fmt_price, fmt_change, format_signal_message, format_market_overview,
    main_menu_keyboard, coin_list_keyboard, timeframe_keyboard,
    signal_detail_keyboard, academy_keyboard, lesson_list_keyboard,
    watchlist_keyboard, settings_keyboard, settings_tf_keyboard,
    back_home_row,
)

logger = logging.getLogger(__name__)

# ─── Helpers ──────────────────────────────────────────────────────────────────

async def safe_edit(query, text: str, keyboard=None, parse_mode=ParseMode.HTML):
    """Edit message safely, handling unchanged content errors."""
    try:
        await query.edit_message_text(
            text, reply_markup=keyboard, parse_mode=parse_mode
        )
    except Exception as e:
        if "not modified" not in str(e).lower():
            logger.warning("safe_edit: %s", e)


async def safe_reply(update: Update, text: str, keyboard=None, parse_mode=ParseMode.HTML):
    """Send reply safely."""
    try:
        await update.message.reply_text(
            text, reply_markup=keyboard, parse_mode=parse_mode
        )
    except Exception as e:
        logger.warning("safe_reply: %s", e)


# ─── Home / Dashboard ─────────────────────────────────────────────────────────

WELCOME_TEXT = (
    "🌟 <b>Halol Crypto AI</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Your halal spot crypto assistant.\n\n"
    "📊 Technical Analysis\n"
    "🏦 Smart Money Concepts\n"
    "🎯 Trade Plans with Stop Loss & Take Profit\n"
    "🎓 Education & Lessons\n\n"
    "⚠️ <i>Halal only: Spot trading. No futures. No leverage.</i>\n\n"
    "Choose an option below:"
)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await upsert_user(user.id, user.username or "", user.first_name or "")

    keyboard = main_menu_keyboard()

    # Add Mini App button if configured
    if WEBAPP_URL and WEBAPP_URL != "https://your-domain.com":
        from telegram import WebAppInfo
        webapp_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🚀 Open Dashboard",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )],
            *keyboard.inline_keyboard,
        ])
        keyboard = webapp_kb

    await safe_reply(update, WELCOME_TEXT, keyboard)


async def cmd_home(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, ctx)


# ─── Main Menu Router ─────────────────────────────────────────────────────────

async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data  = query.data
    user  = update.effective_user

    # Ensure user exists
    await upsert_user(user.id, user.username or "", user.first_name or "")

    # ── Navigation ─────────────────────────────────────────────────────────
    if data in ("home", "back"):
        await safe_edit(query, WELCOME_TEXT, main_menu_keyboard())
        return

    # ── Signals ────────────────────────────────────────────────────────────
    if data == "menu_signals":
        await show_coin_picker(query, "signal_coin", title="📈 <b>Select a Coin for Analysis</b>")
        return

    if data.startswith("coinpage:"):
        parts = data.split(":")
        prefix = parts[1]
        page   = int(parts[2])
        title  = "📈 <b>Select a Coin</b>" if "signal" in prefix else "⭐ <b>Add to Watchlist</b>"
        await show_coin_picker(query, prefix, page=page, title=title)
        return

    if data.startswith("signal_coin:"):
        symbol = data.split(":")[1]
        await show_timeframe_picker(query, symbol)
        return

    if data.startswith("tf:"):
        _, symbol, tf = data.split(":")
        await show_signal(query, user.id, symbol, tf)
        return

    if data.startswith("change_tf:"):
        symbol = data.split(":")[1]
        await show_timeframe_picker(query, symbol)
        return

    if data.startswith("refresh_signal:"):
        symbol = data.split(":")[1]
        settings = await get_user_settings(user.id)
        tf = settings.get("default_tf", "4h")
        await show_signal(query, user.id, symbol, tf)
        return

    # ── Top Opportunities ──────────────────────────────────────────────────
    if data == "menu_top":
        await show_top_opportunities(query, user.id)
        return

    # ── Watchlist ──────────────────────────────────────────────────────────
    if data == "menu_watchlist":
        await show_watchlist(query, user.id)
        return

    if data == "wl_browse":
        await show_coin_picker(query, "wl_add_coin", title="⭐ <b>Add to Watchlist</b>")
        return

    if data.startswith("wl_add_coin:"):
        symbol = data.split(":")[1]
        added = await add_to_watchlist(user.id, symbol)
        if added:
            await query.answer(f"⭐ {symbol} added to watchlist!", show_alert=False)
        else:
            await query.answer(f"{symbol} is already in your watchlist.", show_alert=False)
        await show_watchlist(query, user.id)
        return

    if data.startswith("wl_add:"):
        symbol = data.split(":")[1]
        added = await add_to_watchlist(user.id, symbol)
        msg = f"⭐ {symbol} added to watchlist!" if added else f"{symbol} already in watchlist."
        await query.answer(msg, show_alert=False)
        settings = await get_user_settings(user.id)
        tf = settings.get("default_tf", "4h")
        await show_signal(query, user.id, symbol, tf)
        return

    if data.startswith("wl_remove:"):
        symbol = data.split(":")[1]
        removed = await remove_from_watchlist(user.id, symbol)
        if removed:
            await query.answer(f"❌ {symbol} removed.", show_alert=False)
        await show_watchlist(query, user.id)
        return

    # ── Market Overview ────────────────────────────────────────────────────
    if data == "menu_market":
        await show_market_overview(query)
        return

    # ── Academy ────────────────────────────────────────────────────────────
    if data == "menu_academy" or data == "menu_ai":
        await show_academy(query)
        return

    if data.startswith("academy_cat:"):
        category = data.split(":")[1]
        await show_lesson_list(query, category)
        return

    if data.startswith("lesson:"):
        lesson_key = data.split(":")[1]
        await show_lesson(query, lesson_key)
        return

    # ── Settings ───────────────────────────────────────────────────────────
    if data == "menu_settings":
        await show_settings(query, user.id)
        return

    if data == "settings_tf":
        await safe_edit(
            query,
            "⏱ <b>Select Default Timeframe</b>",
            settings_tf_keyboard()
        )
        return

    if data.startswith("set_tf:"):
        tf = data.split(":")[1]
        await update_user_settings(user.id, default_tf=tf)
        await query.answer(f"✅ Default timeframe set to {tf.upper()}")
        await show_settings(query, user.id)
        return

    if data == "settings_alerts":
        settings = await get_user_settings(user.id)
        current  = settings.get("alert_enabled", 1)
        new_val  = 0 if current else 1
        await update_user_settings(user.id, alert_enabled=new_val)
        await query.answer(f"Alerts {'enabled 🔔' if new_val else 'disabled 🔕'}")
        await show_settings(query, user.id)
        return

    logger.debug("Unhandled callback: %s", data)


# ─── Page Renderers ───────────────────────────────────────────────────────────

async def show_coin_picker(query, callback_prefix: str, page: int = 0, title: str = "📈 <b>Select a Coin</b>"):
    keyboard = coin_list_keyboard(HALAL_COINS, page=page, per_page=10, callback_prefix=callback_prefix)
    await safe_edit(query, title, keyboard)


async def show_timeframe_picker(query, symbol: str):
    coin_name = next((c["name"] for c in HALAL_COINS if c["symbol"] == symbol), symbol)
    text = (
        f"📈 <b>{symbol}</b> — {coin_name}\n\n"
        f"Select analysis timeframe:"
    )
    await safe_edit(query, text, timeframe_keyboard(symbol))


async def show_signal(query, user_id: int, symbol: str, timeframe: str):
    await safe_edit(query, f"⏳ <b>Analyzing {symbol} on {timeframe.upper()}...</b>\n\nFetching candles...")

    try:
        # Fetch data concurrently
        candles_task = fetch_candles(symbol, timeframe)
        ticker_task  = fetch_ticker_24h(symbol)
        candles, ticker = await asyncio.gather(candles_task, ticker_task)

        if not candles:
            await safe_edit(
                query,
                f"⚠️ <b>Could not fetch data for {symbol}</b>\n\nPlease try again.",
                InlineKeyboardMarkup([back_home_row()])
            )
            return

        price     = ticker.get("price", candles[-1]["close"] if candles else 0)
        change_24h = ticker.get("change_24h", 0)

        result = analyze_signal(symbol, timeframe, candles, price, change_24h)

        watchlist = await get_watchlist(user_id)
        in_wl     = symbol in watchlist

        msg      = format_signal_message(result)
        keyboard = signal_detail_keyboard(symbol, in_watchlist=in_wl)
        await safe_edit(query, msg, keyboard)

    except Exception as e:
        logger.exception("show_signal error: %s", e)
        await safe_edit(
            query,
            f"❌ Error analyzing {symbol}. Please try again.",
            InlineKeyboardMarkup([back_home_row()])
        )


async def show_top_opportunities(query, user_id: int):
    await safe_edit(query, "⏳ <b>Scanning top opportunities...</b>")

    try:
        # Quick scan of top 8 coins on 4H
        top_symbols = ["BTC", "ETH", "BNB", "SOL", "ADA", "LINK", "AVAX", "TON"]
        results = []

        tasks = [
            asyncio.gather(
                fetch_candles(sym, "4h", 100),
                fetch_ticker_24h(sym)
            )
            for sym in top_symbols
        ]
        data = await asyncio.gather(*tasks, return_exceptions=True)

        for sym, d in zip(top_symbols, data):
            if isinstance(d, Exception):
                continue
            candles, ticker = d
            if not candles:
                continue
            price = ticker.get("price", candles[-1]["close"])
            change = ticker.get("change_24h", 0)
            signal = analyze_signal(sym, "4h", candles, price, change)
            results.append(signal)

        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)

        msg = "🔥 <b>Top Opportunities (4H)</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        rows = []
        for r in results[:6]:
            msg += (
                f"{r.signal_type} <b>{r.symbol}</b>\n"
                f"  Score: {r.score:.0f}/100  |  {fmt_price(r.price)}  {fmt_change(r.change_24h)}\n\n"
            )
            rows.append([InlineKeyboardButton(
                f"📈 Analyze {r.symbol}",
                callback_data=f"tf:{r.symbol}:4h"
            )])

        rows.append(back_home_row())
        await safe_edit(query, msg, InlineKeyboardMarkup(rows))

    except Exception as e:
        logger.exception("show_top_opportunities: %s", e)
        await safe_edit(
            query,
            "❌ Error scanning opportunities. Please try again.",
            InlineKeyboardMarkup([back_home_row()])
        )


async def show_watchlist(query, user_id: int):
    symbols = await get_watchlist(user_id)
    if not symbols:
        msg = (
            "⭐ <b>Your Watchlist</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Your watchlist is empty.\n\n"
            "Add coins to receive alerts and quick access to signals."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Coins", callback_data="wl_browse")],
            back_home_row(),
        ])
        await safe_edit(query, msg, keyboard)
        return

    # Fetch prices
    data = await fetch_watchlist_data(symbols)
    msg  = "⭐ <b>Your Watchlist</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    for coin in data:
        msg += (
            f"<b>{coin['symbol']}</b> {fmt_price(coin['price'])} "
            f"{fmt_change(coin['change'])}\n"
        )

    keyboard = watchlist_keyboard(symbols)
    await safe_edit(query, msg, keyboard)


async def show_market_overview(query):
    await safe_edit(query, "⏳ <b>Loading market data...</b>")
    try:
        coins_task     = fetch_market_overview()
        sentiment_task = fetch_global_sentiment()
        coins, sentiment = await asyncio.gather(coins_task, sentiment_task)
        msg = format_market_overview(coins, sentiment)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="menu_market")],
            back_home_row(),
        ])
        await safe_edit(query, msg, keyboard)
    except Exception as e:
        logger.exception("show_market_overview: %s", e)
        await safe_edit(query, "❌ Error loading market data.", InlineKeyboardMarkup([back_home_row()]))


async def show_academy(query):
    msg = (
        "🎓 <b>Halol Crypto Academy</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Learn everything about halal crypto investing.\n"
        "Select a topic below:"
    )
    await safe_edit(query, msg, academy_keyboard())


async def show_lesson_list(query, category: str):
    lessons = get_lessons_by_category(category)
    cat_label = CATEGORIES.get(category, "Lessons")
    msg = f"📚 <b>{cat_label}</b>\n━━━━━━━━━━━━━━━━━━━━━\n\nSelect a lesson:"
    keyboard = lesson_list_keyboard(category, lessons)
    await safe_edit(query, msg, keyboard)


async def show_lesson(query, lesson_key: str):
    lesson = get_lesson(lesson_key)
    if not lesson:
        await query.answer("Lesson not found.", show_alert=True)
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Back to Topics", callback_data=f"academy_cat:{lesson['category']}")],
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
    ])
    await safe_edit(query, lesson["content"].strip(), keyboard)


async def show_settings(query, user_id: int):
    settings = await get_user_settings(user_id)
    msg = (
        f"⚙️ <b>Settings</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Default Timeframe: <b>{settings.get('default_tf', '4h').upper()}</b>\n"
        f"Alerts: <b>{'Enabled 🔔' if settings.get('alert_enabled') else 'Disabled 🔕'}</b>\n"
    )
    await safe_edit(query, msg, settings_keyboard(settings))


# ─── Error Handler ────────────────────────────────────────────────────────────

async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error("Update %s caused error: %s", update, ctx.error, exc_info=True)


# ─── Background Alert Scanner ─────────────────────────────────────────────────

async def background_scanner(app: Application):
    """Periodically scan watchlists and send alerts."""
    from config import SCANNER_INTERVAL
    from database import get_all_watchlist_users, save_signal

    while True:
        try:
            await asyncio.sleep(SCANNER_INTERVAL)
            pairs = await get_all_watchlist_users()
            logger.info("Background scan: %d watchlist pairs", len(pairs))

            # Batch by symbol to avoid duplicate fetches
            by_symbol: dict = {}
            for row in pairs:
                sym = row["symbol"]
                if sym not in by_symbol:
                    by_symbol[sym] = []
                by_symbol[sym].append(row["user_id"])

            for sym, user_ids in by_symbol.items():
                try:
                    candles, ticker = await asyncio.gather(
                        fetch_candles(sym, "4h", 100),
                        fetch_ticker_24h(sym),
                    )
                    if not candles:
                        continue
                    price  = ticker.get("price", candles[-1]["close"])
                    change = ticker.get("change_24h", 0)
                    result = analyze_signal(sym, "4h", candles, price, change)

                    # Save to history
                    await save_signal(sym, "4h", result.signal_type, result.score, price)

                    # Alert on Strong Buy
                    if result.score >= 75:
                        msg = (
                            f"🚨 <b>Strong Signal Alert!</b>\n\n"
                            f"{result.signal_type} <b>{sym}</b>\n"
                            f"Score: {result.score:.0f}/100\n"
                            f"Price: {fmt_price(price)}  {fmt_change(change)}\n\n"
                            f"📊 Use /start to view the full analysis."
                        )
                        for uid in user_ids:
                            try:
                                await app.bot.send_message(
                                    uid, msg, parse_mode=ParseMode.HTML
                                )
                            except Exception:
                                pass

                    await asyncio.sleep(0.5)  # Rate limit
                except Exception as e:
                    logger.warning("Scanner error for %s: %s", sym, e)

        except Exception as e:
            logger.error("Background scanner error: %s", e)


# ─── App Builder ──────────────────────────────────────────────────────────────

def build_app() -> Application:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set!")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Handlers
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("home",   cmd_home))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)

    return app


async def main():
    """Entry point — polling mode."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/halol.log"),
        ],
    )

    await init_db()
    app = build_app()

    # Start background scanner as a background task
    asyncio.create_task(background_scanner(app))

    logger.info("🌟 Halol Crypto AI bot starting...")
    await app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
