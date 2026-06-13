"""
Custom Aiogram filters.
"""
from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from core.config import settings


class IsAdmin(BaseFilter):
    """Filter that passes only for admin users."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        if not user:
            return False
        return user.id in settings.admin_ids_list


class IsNotBanned(BaseFilter):
    """Filter that blocks banned users."""

    async def __call__(self, event: Message | CallbackQuery, **data) -> bool:
        db_user = data.get("db_user")
        if db_user is None:
            return True  # No user record = not banned
        return not db_user.is_banned
