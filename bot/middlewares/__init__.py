"""
Anti-spam and rate limiting middleware.
Implements per-user cooldowns and flood protection.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from services.cache import rate_limit_cache
from services.user import user_service
from core.config import settings
from core.logging_config import get_logger
from utils.i18n import t

logger = get_logger(__name__)


class AntiSpamMiddleware(BaseMiddleware):
    """Rate limiting middleware. Tracks message count per user per time window."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = event.from_user
        if not user:
            return await handler(event, data)

        user_id = user.id

        # Skip rate limiting for admins
        if user_id in settings.admin_ids_list:
            return await handler(event, data)

        key = f"{user_id}:messages"
        count = await rate_limit_cache.increment(
            key,
            ttl=settings.RATE_LIMIT_PERIOD,
        )

        if count > settings.RATE_LIMIT_MESSAGES:
            # Calculate remaining seconds
            ttl = await rate_limit_cache.get_ttl(key)
            lang = data.get("user_lang", "uz")
            await event.answer(t("error_rate_limit", lang, seconds=max(ttl, 1)))
            logger.warning("rate_limit_triggered", user_id=user_id, count=count)
            return  # Block the handler

        return await handler(event, data)


class BanCheckMiddleware(BaseMiddleware):
    """Checks if user is banned before processing any event."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = event.from_user
        if not user:
            return await handler(event, data)

        if user.id in settings.admin_ids_list:
            return await handler(event, data)

        # Cache ban status to reduce DB hits
        cache_key = f"ban:{user.id}"
        banned = await rate_limit_cache.get(cache_key)

        if banned is None:
            banned = await user_service.is_banned(user.id)
            await rate_limit_cache.set(cache_key, banned, ttl=300)  # Cache 5 min

        if banned:
            lang = data.get("user_lang", "uz")
            await event.answer(t("error_banned", lang))
            return

        return await handler(event, data)


class UserContextMiddleware(BaseMiddleware):
    """
    Attaches user language and DB user to handler data.
    Must run before other middlewares that need lang.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif hasattr(event, "from_user"):
            tg_user = event.from_user

        if tg_user:
            try:
                db_user, created = await user_service.get_or_create_user(
                    user_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name or "",
                    last_name=tg_user.last_name,
                    telegram_language=tg_user.language_code,
                )
                data["db_user"] = db_user
                data["user_lang"] = db_user.language.value
            except ValueError as e:
                if "user_limit_reached" in str(e):
                    if isinstance(event, Message):
                        from utils.i18n import t
                        await event.answer(t("error_user_limit", "uz"))
                    return
                raise
            except Exception as e:
                logger.error("user_context_error", user_id=tg_user.id, error=str(e))
                data["user_lang"] = "uz"
                data["db_user"] = None

        return await handler(event, data)
