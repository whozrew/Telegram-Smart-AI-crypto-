"""
Watchlist handler.
"""
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards import watchlist_keyboard, back_keyboard
from services.favorites import watchlist_service
from utils.i18n import t
from core.logging_config import get_logger

logger = get_logger(__name__)
router = Router(name="watchlist")


@router.message(Command("watchlist"))
@router.message(F.text.func(lambda x: x in ["👁 Kuzatuv", "👁 Список наблюдения", "👁 Watchlist"]))
async def cmd_watchlist(message: Message, db_user, user_lang: str):
    user_id = db_user.id if db_user else message.from_user.id
    items = await watchlist_service.get_watchlist(user_id)

    if not items:
        await message.answer(t("watchlist_empty", user_lang))
        return

    header = {
        "uz": f"👁 <b>Kuzatuv ro'yxati</b> ({len(items)} ta):",
        "ru": f"👁 <b>Список наблюдения</b> ({len(items)} товаров):",
        "en": f"👁 <b>Watchlist</b> ({len(items)} items):",
    }.get(user_lang, f"👁 Watchlist ({len(items)}):")

    await message.answer(
        header,
        reply_markup=watchlist_keyboard(user_lang, items),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("watch_remove:"))
async def cb_watch_remove(callback: CallbackQuery, db_user, user_lang: str):
    product_id = int(callback.data.split(":")[1])
    user_id = db_user.id if db_user else callback.from_user.id

    removed = await watchlist_service.remove_from_watchlist(user_id, product_id)
    if removed:
        await callback.answer(t("product_removed", user_lang))
        items = await watchlist_service.get_watchlist(user_id)
        if items:
            try:
                await callback.message.edit_reply_markup(
                    reply_markup=watchlist_keyboard(user_lang, items)
                )
            except Exception:
                pass
        else:
            try:
                await callback.message.edit_text(t("watchlist_empty", user_lang))
            except Exception:
                pass
    else:
        await callback.answer(t("error_generic", user_lang), show_alert=True)


@router.callback_query(F.data.startswith("watch_view:"))
async def cb_watch_view(callback: CallbackQuery, db_user, user_lang: str):
    await callback.answer()
    product_id = int(callback.data.split(":")[1])
    user_id = db_user.id if db_user else callback.from_user.id

    items = await watchlist_service.get_watchlist(user_id)
    item = next((i for i in items if i["product_id"] == product_id), None)

    if not item:
        await callback.answer(t("error_generic", user_lang), show_alert=True)
        return

    price = item.get("price")
    price_str = f"{price:,.0f} {item.get('currency', 'UZS')}" if price else t("no_price", user_lang)
    avail = t("in_stock", user_lang) if item.get("availability") else t("out_of_stock", user_lang)

    text = (
        f"👁 <b>{item['title']}</b>\n\n"
        f"💰 {price_str}\n"
        f"📦 {avail}\n"
        f"🏪 {item.get('store', '')}\n\n"
        f"🔗 <a href='{item.get('product_url', '')}'>Open</a>"
    )

    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_keyboard(user_lang))
