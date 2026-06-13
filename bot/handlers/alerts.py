"""
Price alerts handler.
Handles alert setup, listing, and removal.
"""
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.keyboards import alerts_keyboard, cancel_keyboard, main_menu_keyboard
from services.favorites import alert_service
from services.session import get_session_product
from database.models import AlertType
from utils.i18n import t
from core.logging_config import get_logger

logger = get_logger(__name__)
router = Router(name="alerts")


class AlertStates(StatesGroup):
    waiting_for_price = State()


# Temp storage for alert context during FSM
_alert_context: dict[int, dict] = {}


async def start_alert_setup(
    callback: CallbackQuery,
    session_id: str,
    product_index: int,
    lang: str,
    db_user,
) -> None:
    """Called from search handler when Track button is pressed."""
    product = await get_session_product(session_id, product_index)
    if not product:
        await callback.message.answer(t("error_generic", lang))
        return

    user_id = db_user.id if db_user else callback.from_user.id
    _alert_context[user_id] = {
        "product": product,
        "session_id": session_id,
        "product_index": product_index,
    }

    current_price = product.get("price")
    price_hint = ""
    if current_price:
        price_hint = f"\n\n💰 Hozirgi narx: {current_price:,.0f} {product.get('currency', 'UZS')}"

    await callback.message.answer(
        t("alert_prompt", lang) + price_hint,
        reply_markup=cancel_keyboard(lang),
    )


@router.message(Command("alerts"))
@router.message(F.text.func(lambda x: x in ["🔔 Ogohlantirishlar", "🔔 Оповещения", "🔔 Alerts"]))
async def cmd_alerts(message: Message, db_user, user_lang: str):
    user_id = db_user.id if db_user else message.from_user.id
    alerts = await alert_service.get_user_alerts(user_id)

    if not alerts:
        await message.answer(t("watchlist_empty", user_lang))
        return

    await message.answer(
        f"🔔 <b>{'Ogohlantirishlar' if user_lang == 'uz' else 'Оповещения' if user_lang == 'ru' else 'Alerts'}</b> ({len(alerts)}):",
        reply_markup=alerts_keyboard(user_lang, alerts),
        parse_mode="HTML",
    )


@router.message(F.text.regexp(r"^\d[\d\s,.]*$"))
async def handle_price_input(message: Message, db_user, user_lang: str):
    """Handle numeric price input for alert setup."""
    user_id = db_user.id if db_user else message.from_user.id
    ctx = _alert_context.get(user_id)
    if not ctx:
        return  # Not in alert setup mode, ignore number

    price_text = message.text.replace(" ", "").replace(",", "").replace(".", "")
    try:
        target_price = float(price_text)
        if target_price <= 0:
            raise ValueError("non-positive")
    except ValueError:
        await message.answer(t("alert_invalid_price", user_lang))
        return

    product = ctx["product"]
    await alert_service.set_alert(
        user_id=user_id,
        product_data=product,
        target_price=target_price,
        alert_type=AlertType.INSTANT,
    )

    del _alert_context[user_id]

    currency = product.get("currency", "UZS")
    await message.answer(
        t("alert_set", user_lang, price=f"{target_price:,.0f} {currency}"),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("alert_remove:"))
async def cb_alert_remove(callback: CallbackQuery, db_user, user_lang: str):
    alert_id = int(callback.data.split(":")[1])
    user_id = db_user.id if db_user else callback.from_user.id
    removed = await alert_service.remove_alert(user_id, alert_id)

    if removed:
        await callback.answer(t("product_removed", user_lang))
        # Refresh list
        alerts = await alert_service.get_user_alerts(user_id)
        if alerts:
            try:
                await callback.message.edit_reply_markup(
                    reply_markup=alerts_keyboard(user_lang, alerts)
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


@router.callback_query(F.data.startswith("alert_view:"))
async def cb_alert_view(callback: CallbackQuery, db_user, user_lang: str):
    await callback.answer()
    alert_id = int(callback.data.split(":")[1])
    user_id = db_user.id if db_user else callback.from_user.id
    alerts = await alert_service.get_user_alerts(user_id)
    alert = next((a for a in alerts if a["alert_id"] == alert_id), None)
    if not alert:
        await callback.answer(t("error_generic", user_lang), show_alert=True)
        return

    price_str = f"{alert['target_price']:,.0f} {alert['currency']}"
    current = alert.get("current_price")
    current_str = f"{current:,.0f} {alert['currency']}" if current else "N/A"

    text = (
        f"🔔 <b>{alert['title'][:50]}</b>\n\n"
        f"🎯 Target: {price_str}\n"
        f"💰 Current: {current_str}\n"
        f"🏪 Store: {alert['store']}"
    )
    await callback.message.answer(text, parse_mode="HTML")
