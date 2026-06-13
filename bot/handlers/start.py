"""
Start, help, and language handlers.
"""
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards import (
    main_menu_keyboard,
    language_keyboard,
    settings_keyboard,
)
from services.user import user_service
from utils.i18n import t

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, db_user, user_lang: str):
    await message.answer(
        t("welcome", user_lang),
        reply_markup=main_menu_keyboard(user_lang),
        parse_mode="HTML",
    )


@router.message(Command("help"))
@router.message(F.text.func(lambda t: t in ["❓ Yordam", "❓ Помощь", "❓ Help"]))
async def cmd_help(message: Message, user_lang: str):
    await message.answer(
        t("help_text", user_lang),
        parse_mode="HTML",
    )


@router.message(Command("language"))
@router.message(F.text.func(lambda t: t in ["🌐 Til", "🌐 Язык", "🌐 Language"]))
async def cmd_language(message: Message, user_lang: str):
    await message.answer(
        t("language_select", user_lang),
        reply_markup=language_keyboard(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def cb_language_select(callback: CallbackQuery, db_user, user_lang: str):
    lang = callback.data.split(":")[1]
    if lang not in ("uz", "ru", "en"):
        await callback.answer("Invalid language")
        return

    await user_service.update_language(db_user.id, lang)
    await callback.answer(t("language_changed", lang), show_alert=False)
    await callback.message.edit_text(
        t("language_changed", lang),
    )
    await callback.message.answer(
        t("welcome", lang),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )


@router.message(Command("settings"))
@router.message(F.text.func(lambda t: t in ["⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings"]))
async def cmd_settings(message: Message, user_lang: str):
    lang_display = {"uz": "O'zbek tili 🇺🇿", "ru": "Русский 🇷🇺", "en": "English 🇬🇧"}
    await message.answer(
        t("settings_menu", user_lang, language=lang_display.get(user_lang, "")),
        reply_markup=settings_keyboard(user_lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "settings:language")
async def cb_settings_language(callback: CallbackQuery, user_lang: str):
    await callback.message.edit_text(
        t("language_select", user_lang),
        reply_markup=language_keyboard(),
    )


@router.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery, user_lang: str):
    await callback.answer()
    await callback.message.answer(
        t("welcome", user_lang),
        reply_markup=main_menu_keyboard(user_lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, user_lang: str):
    await callback.answer(t("btn_cancel", user_lang))
    try:
        await callback.message.delete()
    except Exception:
        pass


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()
