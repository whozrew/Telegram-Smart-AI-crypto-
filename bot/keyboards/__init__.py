"""
All Telegram keyboards.
Inline and reply keyboards for all bot flows.
"""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from utils.i18n import t


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=t("btn_search", lang)),
        KeyboardButton(text=t("btn_favorites", lang)),
    )
    builder.row(
        KeyboardButton(text=t("btn_watchlist", lang)),
        KeyboardButton(text=t("btn_alerts", lang)),
    )
    builder.row(
        KeyboardButton(text=t("btn_settings", lang)),
        KeyboardButton(text=t("btn_help", lang)),
    )
    return builder.as_markup(resize_keyboard=True)


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 O'zbekcha", callback_data="lang:uz")
    builder.button(text="🇷🇺 Русский", callback_data="lang:ru")
    builder.button(text="🇬🇧 English", callback_data="lang:en")
    builder.adjust(1)
    return builder.as_markup()


def product_keyboard(
    lang: str,
    product_index: int,
    total_products: int,
    product_url: str,
    product_id: str,
    session_id: str,
    is_saved: bool = False,
) -> InlineKeyboardMarkup:
    """Keyboard for a single product card."""
    builder = InlineKeyboardBuilder()

    # Row 1: AI Advice + Compare
    builder.button(
        text=t("btn_ai_advice", lang),
        callback_data=f"ai:{session_id}:{product_index}",
    )
    builder.button(
        text=t("btn_compare", lang),
        callback_data=f"compare_add:{session_id}:{product_index}",
    )

    # Row 2: Save + Track
    save_text = t("btn_saved", lang) if is_saved else t("btn_save", lang)
    builder.button(
        text=save_text,
        callback_data=f"save:{session_id}:{product_index}",
    )
    builder.button(
        text=t("btn_track", lang),
        callback_data=f"track:{session_id}:{product_index}",
    )

    # Row 3: Open product (URL button)
    builder.button(
        text=t("btn_open", lang),
        url=product_url,
    )

    # Row 4: Navigation
    nav_buttons = []
    if product_index > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text=t("btn_prev", lang),
                callback_data=f"nav:{session_id}:{product_index - 1}",
            )
        )

    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{product_index + 1}/{total_products}",
            callback_data="noop",
        )
    )

    if product_index < total_products - 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text=t("btn_next", lang),
                callback_data=f"nav:{session_id}:{product_index + 1}",
            )
        )

    builder.adjust(2, 2, 1)
    markup = builder.as_markup()

    # Insert nav row manually
    from aiogram.types import InlineKeyboardMarkup
    rows = list(markup.inline_keyboard)
    rows.append(nav_buttons)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def alert_type_keyboard(lang: str, session_id: str, product_index: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⚡ " + ("Darhol xabardor qil" if lang == "uz" else "Мгновенно" if lang == "ru" else "Instant"),
        callback_data=f"alert_type:instant:{session_id}:{product_index}",
    )
    builder.button(
        text="📅 " + ("Kunlik xulosada" if lang == "uz" else "Ежедневно" if lang == "ru" else "Daily"),
        callback_data=f"alert_type:daily:{session_id}:{product_index}",
    )
    builder.button(text=t("btn_cancel", lang), callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def favorites_keyboard(lang: str, favorites: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for fav in favorites:
        price_str = f"{fav['price']:,.0f} {fav['currency']}" if fav.get("price") else t("no_price", lang)
        title = fav["title"][:30] + "..." if len(fav["title"]) > 30 else fav["title"]
        builder.button(
            text=f"🛍 {title} — {price_str}",
            callback_data=f"fav_view:{fav['product_id']}",
        )
        builder.button(
            text="🗑",
            callback_data=f"fav_remove:{fav['product_id']}",
        )

    if favorites:
        builder.adjust(2)

    builder.button(text=t("btn_back", lang), callback_data="back_main")
    builder.adjust(*([2] * len(favorites)), 1)
    return builder.as_markup()


def watchlist_keyboard(lang: str, items: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        title = item["title"][:35] + "..." if len(item["title"]) > 35 else item["title"]
        builder.button(
            text=f"👁 {title}",
            callback_data=f"watch_view:{item['product_id']}",
        )
        builder.button(
            text="🗑",
            callback_data=f"watch_remove:{item['product_id']}",
        )

    if items:
        builder.adjust(*([2] * len(items)))

    builder.button(text=t("btn_back", lang), callback_data="back_main")
    builder.adjust(*([2] * len(items)), 1)
    return builder.as_markup()


def alerts_keyboard(lang: str, alerts: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for alert in alerts:
        title = alert["title"][:30] + "..." if len(alert["title"]) > 30 else alert["title"]
        target = f"{alert['target_price']:,.0f}"
        builder.button(
            text=f"🔔 {title} < {target}",
            callback_data=f"alert_view:{alert['alert_id']}",
        )
        builder.button(
            text="🗑",
            callback_data=f"alert_remove:{alert['alert_id']}",
        )

    if alerts:
        builder.adjust(*([2] * len(alerts)))

    builder.button(text=t("btn_back", lang), callback_data="back_main")
    builder.adjust(*([2] * len(alerts)), 1)
    return builder.as_markup()


def settings_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_language", lang), callback_data="settings:language")
    builder.button(text=t("btn_back", lang), callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()


def compare_keyboard(lang: str, count: int, session_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if count >= 2:
        builder.button(
            text=t("btn_do_compare", lang),
            callback_data=f"do_compare:{session_id}",
        )
    builder.button(
        text=t("btn_clear_compare", lang),
        callback_data=f"compare_clear:{session_id}",
    )
    builder.button(text=t("btn_cancel", lang), callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def confirm_alert_keyboard(
    lang: str,
    session_id: str,
    product_index: int,
    price: float,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("btn_confirm", lang),
        callback_data=f"alert_confirm:{session_id}:{product_index}:{price}",
    )
    builder.button(text=t("btn_cancel", lang), callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()


# ── Admin Keyboards ──────────────────────────────────────────────────────────

def admin_panel_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_stats", lang), callback_data="admin:stats")
    builder.button(text=t("btn_broadcast", lang), callback_data="admin:broadcast")
    builder.button(text=t("btn_ban_user", lang), callback_data="admin:ban")
    builder.button(text=t("btn_unban_user", lang), callback_data="admin:unban")
    builder.adjust(2, 2)
    return builder.as_markup()


def cancel_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_cancel", lang), callback_data="cancel")
    return builder.as_markup()


def back_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_back", lang), callback_data="back_main")
    return builder.as_markup()


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
