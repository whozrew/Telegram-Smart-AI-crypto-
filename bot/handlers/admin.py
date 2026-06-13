"""
Admin panel handler.
Broadcast, stats, ban/unban management.
"""
from __future__ import annotations

import asyncio
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards import admin_panel_keyboard, cancel_keyboard
from services.user import user_service
from services.favorites import alert_service
from database.models import AdminActionType
from core.config import settings
from core.logging_config import get_logger
from utils.i18n import t

logger = get_logger(__name__)
router = Router(name="admin")

# FSM-like state for admin (simple dict since admin is 1-2 people)
_admin_state: dict[int, dict] = {}


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids_list


async def _log_admin_action(
    admin_id: int,
    action: AdminActionType,
    target_user_id: Optional[int] = None,
    details: Optional[str] = None,
) -> None:
    from database.db import get_db_session
    from database.models import AdminLog
    try:
        async with get_db_session() as session:
            session.add(AdminLog(
                admin_id=admin_id,
                action=action,
                target_user_id=target_user_id,
                details=details,
            ))
    except Exception as e:
        logger.error("admin_log_error", error=str(e))


@router.message(Command("admin"))
async def cmd_admin(message: Message, user_lang: str):
    if not is_admin(message.from_user.id):
        await message.answer(t("admin_not_authorized", user_lang))
        return

    await message.answer(
        t("admin_panel", user_lang),
        reply_markup=admin_panel_keyboard(user_lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(callback: CallbackQuery, user_lang: str):
    if not is_admin(callback.from_user.id):
        await callback.answer(t("admin_not_authorized", user_lang), show_alert=True)
        return

    await callback.answer()

    user_stats = await user_service.get_stats()
    alert_stats = await alert_service.get_stats()

    await callback.message.answer(
        t(
            "admin_stats",
            user_lang,
            total_users=user_stats["total_users"],
            active_users=user_stats["active_users"],
            total_searches=user_stats["total_searches"],
            total_alerts=alert_stats["total_alerts"],
            total_favorites=alert_stats["total_favorites"],
            banned_users=user_stats["banned_users"],
        ),
        parse_mode="HTML",
    )
    await _log_admin_action(callback.from_user.id, AdminActionType.VIEW_STATS)


@router.callback_query(F.data == "admin:broadcast")
async def cb_admin_broadcast_start(callback: CallbackQuery, user_lang: str):
    if not is_admin(callback.from_user.id):
        await callback.answer(t("admin_not_authorized", user_lang), show_alert=True)
        return

    await callback.answer()
    _admin_state[callback.from_user.id] = {"action": "broadcast"}
    await callback.message.answer(
        t("admin_broadcast_prompt", user_lang),
        reply_markup=cancel_keyboard(user_lang),
    )


@router.callback_query(F.data == "admin:ban")
async def cb_admin_ban_start(callback: CallbackQuery, user_lang: str):
    if not is_admin(callback.from_user.id):
        await callback.answer(t("admin_not_authorized", user_lang), show_alert=True)
        return

    await callback.answer()
    _admin_state[callback.from_user.id] = {"action": "ban"}
    await callback.message.answer(
        t("admin_ban_prompt", user_lang),
        reply_markup=cancel_keyboard(user_lang),
    )


@router.callback_query(F.data == "admin:unban")
async def cb_admin_unban_start(callback: CallbackQuery, user_lang: str):
    if not is_admin(callback.from_user.id):
        await callback.answer(t("admin_not_authorized", user_lang), show_alert=True)
        return

    await callback.answer()
    _admin_state[callback.from_user.id] = {"action": "unban"}
    await callback.message.answer(
        "Enter user ID to unban:",
        reply_markup=cancel_keyboard(user_lang),
    )


@router.message(F.from_user.func(lambda u: u.id in settings.admin_ids_list if u else False))
async def handle_admin_input(message: Message, bot: Bot, user_lang: str):
    """Handle admin state-based input (broadcast message, ban/unban user ID)."""
    admin_id = message.from_user.id
    state = _admin_state.get(admin_id)
    if not state:
        return  # No active admin action, let other handlers process

    action = state.get("action")

    if action == "broadcast":
        del _admin_state[admin_id]
        await _do_broadcast(message, bot, admin_id, user_lang)

    elif action == "ban":
        del _admin_state[admin_id]
        try:
            target_id = int(message.text.strip())
        except ValueError:
            await message.answer("Invalid user ID.")
            return
        await user_service.ban_user(target_id, admin_id)
        await message.answer(t("admin_banned", user_lang, user_id=target_id))
        await _log_admin_action(admin_id, AdminActionType.BAN, target_user_id=target_id)

    elif action == "unban":
        del _admin_state[admin_id]
        try:
            target_id = int(message.text.strip())
        except ValueError:
            await message.answer("Invalid user ID.")
            return
        await user_service.unban_user(target_id)
        await message.answer(t("admin_unbanned", user_lang, user_id=target_id))
        await _log_admin_action(admin_id, AdminActionType.UNBAN, target_user_id=target_id)


async def _do_broadcast(message: Message, bot: Bot, admin_id: int, user_lang: str) -> None:
    """Broadcast a message to all active users."""
    user_ids = await user_service.get_all_active_user_ids()
    sent = 0
    failed = 0

    status_msg = await message.answer(f"📢 Broadcasting to {len(user_ids)} users...")

    for uid in user_ids:
        try:
            # Forward original message content
            if message.photo:
                await bot.send_photo(
                    chat_id=uid,
                    photo=message.photo[-1].file_id,
                    caption=message.caption or "",
                    parse_mode="HTML",
                )
            elif message.video:
                await bot.send_video(
                    chat_id=uid,
                    video=message.video.file_id,
                    caption=message.caption or "",
                    parse_mode="HTML",
                )
            elif message.document:
                await bot.send_document(
                    chat_id=uid,
                    document=message.document.file_id,
                    caption=message.caption or "",
                    parse_mode="HTML",
                )
            else:
                await bot.send_message(
                    chat_id=uid,
                    text=message.text or "",
                    parse_mode="HTML",
                )
            sent += 1
        except Exception as e:
            failed += 1
            logger.warning("broadcast_failed", uid=uid, error=str(e))

        # Rate limiting: 30 messages/second max
        if sent % 30 == 0:
            await asyncio.sleep(1)

    try:
        await status_msg.edit_text(
            t("admin_broadcast_done", user_lang, count=sent) + f"\n❌ Failed: {failed}"
        )
    except Exception:
        await message.answer(t("admin_broadcast_done", user_lang, count=sent))

    await _log_admin_action(
        admin_id,
        AdminActionType.BROADCAST,
        details=f"sent={sent}, failed={failed}",
    )
