"""
User service — all user-related DB operations.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db_session
from database.models import User, BannedUser, SearchHistory, LanguageCode
from core.config import settings
from core.logging_config import get_logger
from utils.i18n import detect_language

logger = get_logger(__name__)


class UserService:

    async def get_or_create_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: str,
        last_name: Optional[str],
        telegram_language: Optional[str] = None,
    ) -> tuple[User, bool]:
        """
        Get existing user or create new one.
        Returns (user, created).
        Raises ValueError if user limit reached for new users.
        """
        async with get_db_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if user:
                # Update last active and basic info
                user.last_active_at = datetime.utcnow()
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                # Mark admin if in admin list
                if user_id in settings.admin_ids_list:
                    user.is_admin = True
                await session.flush()
                return user, False

            # Check user limit for new users
            count_result = await session.execute(
                select(func.count(User.id)).where(User.is_active == True)
            )
            active_count = count_result.scalar_one()

            if active_count >= settings.MAX_ACTIVE_USERS:
                raise ValueError("user_limit_reached")

            # Create new user
            lang = detect_language(telegram_language)
            new_user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language=LanguageCode(lang),
                is_active=True,
                is_admin=user_id in settings.admin_ids_list,
                last_active_at=datetime.utcnow(),
            )
            session.add(new_user)
            await session.flush()
            logger.info("user_created", user_id=user_id, lang=lang)
            return new_user, True

    async def get_user(self, user_id: int) -> Optional[User]:
        async with get_db_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()

    async def update_language(self, user_id: int, language: str) -> None:
        async with get_db_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(language=LanguageCode(language))
            )

    async def is_banned(self, user_id: int) -> bool:
        async with get_db_session() as session:
            result = await session.execute(
                select(BannedUser).where(
                    BannedUser.user_id == user_id,
                    BannedUser.is_active == True,
                )
            )
            return result.scalar_one_or_none() is not None

    async def ban_user(self, user_id: int, banned_by: int, reason: Optional[str] = None) -> None:
        async with get_db_session() as session:
            # Check if already banned
            result = await session.execute(
                select(BannedUser).where(BannedUser.user_id == user_id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.is_active = True
                existing.banned_by = banned_by
                existing.reason = reason
                existing.banned_at = datetime.utcnow()
                existing.unbanned_at = None
            else:
                session.add(BannedUser(
                    user_id=user_id,
                    banned_by=banned_by,
                    reason=reason,
                    is_active=True,
                ))
            # Also update User record
            await session.execute(
                update(User).where(User.id == user_id).values(is_banned=True)
            )
            logger.info("user_banned", user_id=user_id, by=banned_by)

    async def unban_user(self, user_id: int) -> None:
        async with get_db_session() as session:
            await session.execute(
                update(BannedUser)
                .where(BannedUser.user_id == user_id)
                .values(is_active=False, unbanned_at=datetime.utcnow())
            )
            await session.execute(
                update(User).where(User.id == user_id).values(is_banned=False)
            )
            logger.info("user_unbanned", user_id=user_id)

    async def record_search(
        self,
        user_id: int,
        query: str,
        result_count: int,
        search_type: str = "text",
    ) -> None:
        async with get_db_session() as session:
            session.add(SearchHistory(
                user_id=user_id,
                query=query,
                result_count=result_count,
                search_type=search_type,
            ))

    async def get_stats(self) -> dict:
        async with get_db_session() as session:
            total = (await session.execute(select(func.count(User.id)))).scalar_one()
            active = (await session.execute(
                select(func.count(User.id)).where(User.is_active == True)
            )).scalar_one()
            banned = (await session.execute(
                select(func.count(BannedUser.id)).where(BannedUser.is_active == True)
            )).scalar_one()
            searches = (await session.execute(select(func.count(SearchHistory.id)))).scalar_one()

            return {
                "total_users": total,
                "active_users": active,
                "banned_users": banned,
                "total_searches": searches,
            }

    async def get_all_active_user_ids(self) -> list[int]:
        async with get_db_session() as session:
            result = await session.execute(
                select(User.id).where(User.is_active == True, User.is_banned == False)
            )
            return [row[0] for row in result.fetchall()]


user_service = UserService()
