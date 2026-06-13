"""
Favorites handler.
"""
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards import favorites_keyboard, back_keyboard
from services.favorites import favorites_service
from utils.i18n import t
from core.logging_config import get_logger

logger = get_logger(__name__)
router = Router(name="favorites")


@router.message(Command("favorites"))
@router.message(F.text.func(lambda x: x in ["⭐ Saqlangan", "⭐ Избранное", "⭐ Favorites"]))
async def cmd_favorites(message: Message, db_user, user_lang: str):
    user_id = db_user.id if db_user else message.from_user.id
    favorites = await favorites_service.get_favorites(user_id)

    if not favorites:
        await message.answer(t("favorites_empty", user_lang), parse_mode="HTML")
        return

    await message.answer(
        t("favorites_header", user_lang, count=len(favorites)),
        reply_markup=favorites_keyboard(user_lang, favorites),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("fav_remove:"))
async def cb_fav_remove(callback: CallbackQuery, db_user, user_lang: str):
    product_id = int(callback.data.split(":")[1])
    user_id = db_user.id if db_user else callback.from_user.id

    removed = await favorites_service.remove_favorite(user_id, product_id)

    if removed:
        await callback.answer(t("product_removed", user_lang))
        favorites = await favorites_service.get_favorites(user_id)
        if favorites:
            try:
                await callback.message.edit_reply_markup(
                    reply_markup=favorites_keyboard(user_lang, favorites)
                )
            except Exception:
                pass
        else:
            try:
                await callback.message.edit_text(
                    t("favorites_empty", user_lang), parse_mode="HTML"
                )
            except Exception:
                pass
    else:
        await callback.answer(t("error_generic", user_lang), show_alert=True)


@router.callback_query(F.data.startswith("fav_view:"))
async def cb_fav_view(callback: CallbackQuery, db_user, user_lang: str):
    await callback.answer()
    product_id = int(callback.data.split(":")[1])
    user_id = db_user.id if db_user else callback.from_user.id

    favorites = await favorites_service.get_favorites(user_id)
    fav = next((f for f in favorites if f["product_id"] == product_id), None)

    if not fav:
        await callback.answer(t("error_generic", user_lang), show_alert=True)
        return

    price = fav.get("price")
    price_str = f"{price:,.0f} {fav.get('currency', 'UZS')}" if price else t("no_price", user_lang)
    avail = t("in_stock", user_lang) if fav.get("availability") else t("out_of_stock", user_lang)

    text = (
        f"⭐ <b>{fav['title']}</b>\n\n"
        f"💰 {price_str}\n"
        f"📦 {avail}\n"
        f"🏪 {fav.get('store', '')}\n\n"
        f"🔗 <a href='{fav.get('product_url', '')}'>Open in store</a>"
    )

    if fav.get("image_url"):
        try:
            await callback.message.answer_photo(
                photo=fav["image_url"],
                caption=text,
                parse_mode="HTML",
                reply_markup=back_keyboard(user_lang),
            )
            return
        except Exception:
            pass

    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_keyboard(user_lang))
