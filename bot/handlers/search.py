"""
Search handler.
Handles text search, URL search, and displays product cards with full navigation.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InputMediaPhoto,
)

from bot.keyboards import (
    product_keyboard,
    main_menu_keyboard,
    compare_keyboard,
    cancel_keyboard,
)
from services.search import search_service
from services.session import (
    create_search_session,
    get_search_session,
    get_session_product,
    add_to_compare,
    clear_compare,
    get_compare_list,
)
from services.favorites import favorites_service
from services.gemini import gemini_service
from services.user import user_service
from core.config import settings
from core.logging_config import get_logger
from utils.i18n import t

logger = get_logger(__name__)
router = Router(name="search")

# Per-user search cooldown cache (in-memory, not Redis, for speed)
_last_search: dict[int, float] = {}


def _format_product_card(product: dict, lang: str) -> str:
    price = product.get("price")
    currency = product.get("currency", "UZS")
    if price:
        price_str = f"{price:,.0f} {currency}"
    else:
        price_str = t("no_price", lang)

    availability = t("in_stock", lang) if product.get("availability") else t("out_of_stock", lang)

    rating = product.get("rating")
    if rating:
        stars = "⭐" * round(float(rating))
        rating_str = f"{stars} ({rating:.1f})"
    else:
        rating_str = t("no_rating", lang)

    last_updated = product.get("last_updated", "")
    if last_updated:
        try:
            dt = datetime.fromisoformat(last_updated)
            updated_str = dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            updated_str = last_updated
    else:
        updated_str = "—"

    return t(
        "product_card",
        lang,
        title=product.get("title", "—"),
        price=price_str,
        availability=availability,
        rating=rating_str,
        store=product.get("store", "—"),
        updated=updated_str,
    )


async def _send_product_card(
    message_or_callback,
    product: dict,
    index: int,
    total: int,
    session_id: str,
    lang: str,
    user_id: int,
    edit: bool = False,
):
    """Send or edit a product card message."""
    text = _format_product_card(product, lang)
    image_url = product.get("image_url")
    product_url = product.get("product_url", "")

    is_saved = bool(await favorites_service.is_favorite(user_id, product_url))

    keyboard = product_keyboard(
        lang=lang,
        product_index=index,
        total_products=total,
        product_url=product_url,
        product_id=str(product.get("external_id") or ""),
        session_id=session_id,
        is_saved=is_saved,
    )

    try:
        if edit and hasattr(message_or_callback, "message"):
            msg = message_or_callback.message
            if image_url:
                try:
                    await msg.edit_media(
                        InputMediaPhoto(media=image_url, caption=text, parse_mode="HTML"),
                        reply_markup=keyboard,
                    )
                    return
                except Exception:
                    pass
            await msg.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
            return
    except Exception:
        pass

    # Fresh send
    target = message_or_callback.message if hasattr(message_or_callback, "message") else message_or_callback
    if image_url:
        try:
            await target.answer_photo(
                photo=image_url,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            return
        except Exception:
            pass  # Fall through to text-only

    await target.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def _do_search(message: Message, query: str, user_id: int, lang: str, search_type: str = "text"):
    """Core search logic shared between text and URL search."""
    # Cooldown check
    import time
    now = time.time()
    last = _last_search.get(user_id, 0)
    if now - last < settings.SEARCH_COOLDOWN:
        remaining = int(settings.SEARCH_COOLDOWN - (now - last)) + 1
        await message.answer(t("error_cooldown", lang, seconds=remaining))
        return
    _last_search[user_id] = now

    searching_msg = await message.answer(t("searching", lang))

    try:
        result = await search_service.search_auto(query, user_id)
    except Exception as e:
        logger.error("search_error", query=query, error=str(e))
        await searching_msg.delete()
        await message.answer(t("error_generic", lang))
        return

    # Record search history
    total = result.get("total", 0)
    await user_service.record_search(user_id, query, total, search_type)

    all_results = result.get("all", [])

    if not all_results:
        await searching_msg.delete()
        await message.answer(t("search_no_results", lang, query=query), parse_mode="HTML")
        return

    # Show count
    await searching_msg.delete()

    # Show exact matches label
    exact = result.get("exact", [])
    similar = result.get("similar", [])

    combined = []
    if exact:
        combined.extend(exact)
    if similar:
        combined.extend(similar)
    if not combined:
        combined = all_results

    session_id = await create_search_session(user_id, combined, query)

    # Header message
    header_text = t("search_results_header", lang, query=query, count=len(combined))
    if exact and similar:
        header_text += f"\n\n{t('exact_matches', lang)}"

    await message.answer(header_text, parse_mode="HTML")

    # Show first product card
    await _send_product_card(
        message,
        combined[0],
        index=0,
        total=len(combined),
        session_id=session_id,
        lang=lang,
        user_id=user_id,
    )


# ─────────────────────────────────────────────
# Command handlers
# ─────────────────────────────────────────────

@router.message(Command("search"))
@router.message(F.text.func(lambda t: t in ["🔍 Qidirish", "🔍 Поиск", "🔍 Search"]))
async def cmd_search(message: Message, user_lang: str):
    await message.answer(t("search_prompt", user_lang))


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_search(message: Message, db_user, user_lang: str):
    """Handle plain text messages as product searches."""
    text = message.text.strip()
    if not text:
        return

    # Skip main menu button texts (handled by their own handlers)
    skip_texts = {
        "⭐ Saqlangan", "⭐ Избранное", "⭐ Favorites",
        "👁 Kuzatuv", "👁 Список наблюдения", "👁 Watchlist",
        "🔔 Ogohlantirishlar", "🔔 Оповещения", "🔔 Alerts",
        "⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings",
        "❓ Yordam", "❓ Помощь", "❓ Help",
        "🌐 Til", "🌐 Язык", "🌐 Language",
        "🔍 Qidirish", "🔍 Поиск", "🔍 Search",
    }
    if text in skip_texts:
        return

    user_id = db_user.id if db_user else message.from_user.id
    await _do_search(message, text, user_id, user_lang)


# ─────────────────────────────────────────────
# Navigation callbacks
# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("nav:"))
async def cb_navigate(callback: CallbackQuery, db_user, user_lang: str):
    await callback.answer()
    _, session_id, index_str = callback.data.split(":")
    index = int(index_str)

    session = await get_search_session(session_id)
    if not session:
        await callback.message.answer(t("error_generic", user_lang))
        return

    results = session.get("results", [])
    if index < 0 or index >= len(results):
        return

    user_id = db_user.id if db_user else callback.from_user.id
    await _send_product_card(
        callback,
        results[index],
        index=index,
        total=len(results),
        session_id=session_id,
        lang=user_lang,
        user_id=user_id,
        edit=True,
    )


# ─────────────────────────────────────────────
# Save (Favorites) callback
# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("save:"))
async def cb_save_product(callback: CallbackQuery, db_user, user_lang: str):
    parts = callback.data.split(":")
    session_id, index_str = parts[1], parts[2]
    index = int(index_str)

    product = await get_session_product(session_id, index)
    if not product:
        await callback.answer(t("error_generic", user_lang), show_alert=True)
        return

    user_id = db_user.id if db_user else callback.from_user.id
    success, reason = await favorites_service.add_favorite(user_id, product)

    if success:
        await callback.answer(t("product_saved", user_lang), show_alert=False)
    else:
        await callback.answer(t("product_already_saved", user_lang), show_alert=False)

    # Refresh the keyboard to show saved state
    session = await get_search_session(session_id)
    results = session.get("results", []) if session else []
    total = len(results)
    product_url = product.get("product_url", "")

    new_keyboard = product_keyboard(
        lang=user_lang,
        product_index=index,
        total_products=total,
        product_url=product_url,
        product_id=str(product.get("external_id") or ""),
        session_id=session_id,
        is_saved=True,
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=new_keyboard)
    except Exception:
        pass


# ─────────────────────────────────────────────
# Track / Watchlist callback
# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("track:"))
async def cb_track_product(callback: CallbackQuery, db_user, user_lang: str):
    from bot.handlers.alerts import start_alert_setup
    parts = callback.data.split(":")
    session_id, index_str = parts[1], parts[2]
    await callback.answer()
    await start_alert_setup(callback, session_id, int(index_str), user_lang, db_user)


# ─────────────────────────────────────────────
# AI Advice callback
# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("ai:"))
async def cb_ai_advice(callback: CallbackQuery, db_user, user_lang: str):
    await callback.answer()
    parts = callback.data.split(":")
    session_id, index_str = parts[1], parts[2]
    index = int(index_str)

    product = await get_session_product(session_id, index)
    if not product:
        await callback.message.answer(t("error_generic", user_lang))
        return

    thinking_msg = await callback.message.answer(t("ai_thinking", user_lang))

    price = product.get("price")
    price_str = f"{price:,.0f} {product.get('currency', 'UZS')}" if price else t("no_price", user_lang)
    rating = product.get("rating")
    rating_str = f"{rating:.1f}/5" if rating else t("no_rating", user_lang)

    advice = await gemini_service.get_ai_advice(
        product_title=product.get("title", ""),
        price=price_str,
        store=product.get("store", ""),
        rating=rating_str,
        language=user_lang,
    )

    await thinking_msg.delete()

    if not advice:
        await callback.message.answer(t("ai_error", user_lang))
        return

    advice_text = t("ai_advice_header", user_lang) + advice
    await callback.message.answer(advice_text, parse_mode="HTML")


# ─────────────────────────────────────────────
# Compare callbacks
# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("compare_add:"))
async def cb_compare_add(callback: CallbackQuery, db_user, user_lang: str):
    parts = callback.data.split(":")
    session_id, index_str = parts[1], parts[2]
    index = int(index_str)

    compare_list, added = await add_to_compare(session_id, index)

    if not added:
        if len(compare_list) >= 5:
            await callback.answer("Max 5 products for comparison", show_alert=True)
        else:
            await callback.answer("Already in compare list", show_alert=True)
        return

    await callback.answer(f"Added to compare ({len(compare_list)}/5)")

    # Show compare panel
    products_text = "\n".join(
        f"{i+1}. {p.get('title', '')[:40]}" for i, p in enumerate(compare_list)
    )

    label = {
        "uz": "Solishtirish ro'yxati",
        "ru": "Список сравнения",
        "en": "Compare list",
    }.get(user_lang, "Compare list")

    await callback.message.answer(
        t("compare_select", user_lang, count=len(compare_list), products=products_text),
        reply_markup=compare_keyboard(user_lang, len(compare_list), session_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("compare_clear:"))
async def cb_compare_clear(callback: CallbackQuery, user_lang: str):
    session_id = callback.data.split(":")[1]
    await clear_compare(session_id)
    await callback.answer("Compare list cleared")
    try:
        await callback.message.delete()
    except Exception:
        pass


@router.callback_query(F.data.startswith("do_compare:"))
async def cb_do_compare(callback: CallbackQuery, user_lang: str):
    await callback.answer()
    session_id = callback.data.split(":")[1]
    compare_list = await get_compare_list(session_id)

    if len(compare_list) < 2:
        await callback.message.answer("Add at least 2 products to compare.")
        return

    # Build comparison table
    lines = [t("compare_result", user_lang), ""]
    for i, p in enumerate(compare_list, 1):
        price = p.get("price")
        price_str = f"{price:,.0f} {p.get('currency', 'UZS')}" if price else "N/A"
        avail = "✅" if p.get("availability") else "❌"
        rating = f"{p.get('rating'):.1f}" if p.get("rating") else "N/A"
        lines.append(
            f"<b>{i}. {p.get('title', '')[:40]}</b>\n"
            f"   💰 {price_str} | ⭐ {rating} | {avail}\n"
            f"   🏪 {p.get('store', '')}"
        )

    await callback.message.answer("\n".join(lines), parse_mode="HTML")

    # Optional: AI comparison
    ai_msg = await callback.message.answer(t("ai_thinking", user_lang))
    ai_result = await gemini_service.compare_products(compare_list, user_lang)
    await ai_msg.delete()

    if ai_result:
        await callback.message.answer(f"🧠 <b>AI Comparison</b>\n\n{ai_result}", parse_mode="HTML")

    await clear_compare(session_id)
