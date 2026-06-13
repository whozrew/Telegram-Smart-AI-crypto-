"""
Favorites and Watchlist service.
"""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from database.db import get_db_session
from database.models import Favorite, Watchlist, Product, Alert, AlertType, PriceHistory
from core.logging_config import get_logger

logger = get_logger(__name__)


def _get_or_create_product_sync(session, product_data: dict):
    """Synchronous helper to be called inside async session."""
    pass  # handled async below


async def _upsert_product(session, product_data: dict) -> Product:
    """Insert or update a product record from scraped data."""
    from sqlalchemy import update as sa_update

    result = await session.execute(
        select(Product).where(
            Product.product_url == product_data["product_url"],
            Product.store == product_data["store"],
        )
    )
    product = result.scalar_one_or_none()

    if product:
        product.title = product_data.get("title", product.title)
        product.price = product_data.get("price")
        product.availability = product_data.get("availability", True)
        product.rating = product_data.get("rating")
        product.image_url = product_data.get("image_url")
        product.external_id = product_data.get("external_id")
    else:
        specs = product_data.get("specifications", {})
        product = Product(
            title=product_data.get("title", "Unknown"),
            price=product_data.get("price"),
            currency=product_data.get("currency", "UZS"),
            availability=product_data.get("availability", True),
            rating=product_data.get("rating"),
            review_count=int(product_data.get("review_count", 0)),
            image_url=product_data.get("image_url"),
            product_url=product_data["product_url"],
            store=product_data.get("store", "Unknown"),
            category=product_data.get("category"),
            brand=product_data.get("brand"),
            specifications=json.dumps(specs) if specs else None,
            external_id=product_data.get("external_id"),
            description=product_data.get("description"),
        )
        session.add(product)

    await session.flush()
    return product


class FavoritesService:

    async def add_favorite(self, user_id: int, product_data: dict) -> tuple[bool, str]:
        """
        Add product to favorites.
        Returns (success, reason).
        """
        async with get_db_session() as session:
            product = await _upsert_product(session, product_data)

            # Check if already favorited
            result = await session.execute(
                select(Favorite).where(
                    Favorite.user_id == user_id,
                    Favorite.product_id == product.id,
                )
            )
            if result.scalar_one_or_none():
                return False, "already_exists"

            session.add(Favorite(user_id=user_id, product_id=product.id))
            logger.info("favorite_added", user_id=user_id, product_id=product.id)
            return True, "added"

    async def remove_favorite(self, user_id: int, product_id: int) -> bool:
        async with get_db_session() as session:
            result = await session.execute(
                delete(Favorite).where(
                    Favorite.user_id == user_id,
                    Favorite.product_id == product_id,
                )
            )
            return result.rowcount > 0

    async def get_favorites(self, user_id: int) -> list[dict]:
        async with get_db_session() as session:
            result = await session.execute(
                select(Favorite)
                .where(Favorite.user_id == user_id)
                .options(selectinload(Favorite.product))
                .order_by(Favorite.created_at.desc())
            )
            favorites = result.scalars().all()
            return [
                {
                    "favorite_id": f.id,
                    "product_id": f.product.id,
                    "title": f.product.title,
                    "price": f.product.price,
                    "currency": f.product.currency,
                    "store": f.product.store,
                    "image_url": f.product.image_url,
                    "product_url": f.product.product_url,
                    "rating": f.product.rating,
                    "availability": f.product.availability,
                    "saved_at": f.created_at.isoformat(),
                }
                for f in favorites
            ]

    async def is_favorite(self, user_id: int, product_url: str) -> Optional[int]:
        """Returns product_id if favorited, else None."""
        async with get_db_session() as session:
            result = await session.execute(
                select(Favorite, Product)
                .join(Product, Favorite.product_id == Product.id)
                .where(
                    Favorite.user_id == user_id,
                    Product.product_url == product_url,
                )
            )
            row = result.first()
            return row[1].id if row else None


class WatchlistService:

    async def add_to_watchlist(self, user_id: int, product_data: dict) -> tuple[bool, str]:
        async with get_db_session() as session:
            product = await _upsert_product(session, product_data)

            result = await session.execute(
                select(Watchlist).where(
                    Watchlist.user_id == user_id,
                    Watchlist.product_id == product.id,
                )
            )
            if result.scalar_one_or_none():
                return False, "already_exists"

            session.add(Watchlist(user_id=user_id, product_id=product.id))
            return True, "added"

    async def get_watchlist(self, user_id: int) -> list[dict]:
        async with get_db_session() as session:
            result = await session.execute(
                select(Watchlist)
                .where(Watchlist.user_id == user_id)
                .options(selectinload(Watchlist.product))
                .order_by(Watchlist.created_at.desc())
            )
            items = result.scalars().all()
            return [
                {
                    "watchlist_id": w.id,
                    "product_id": w.product.id,
                    "title": w.product.title,
                    "price": w.product.price,
                    "currency": w.product.currency,
                    "store": w.product.store,
                    "image_url": w.product.image_url,
                    "product_url": w.product.product_url,
                    "availability": w.product.availability,
                }
                for w in items
            ]

    async def remove_from_watchlist(self, user_id: int, product_id: int) -> bool:
        async with get_db_session() as session:
            result = await session.execute(
                delete(Watchlist).where(
                    Watchlist.user_id == user_id,
                    Watchlist.product_id == product_id,
                )
            )
            return result.rowcount > 0


class AlertService:

    async def set_alert(
        self,
        user_id: int,
        product_data: dict,
        target_price: float,
        alert_type: AlertType = AlertType.INSTANT,
    ) -> int:
        """Set a price alert. Returns alert ID."""
        async with get_db_session() as session:
            product = await _upsert_product(session, product_data)

            # Deactivate any existing alert for this product/user
            existing = await session.execute(
                select(Alert).where(
                    Alert.user_id == user_id,
                    Alert.product_id == product.id,
                    Alert.is_active == True,
                )
            )
            for alert in existing.scalars().all():
                alert.is_active = False

            alert = Alert(
                user_id=user_id,
                product_id=product.id,
                target_price=target_price,
                currency=product_data.get("currency", "UZS"),
                alert_type=alert_type,
                is_active=True,
            )
            session.add(alert)
            await session.flush()
            logger.info("alert_set", user_id=user_id, product_id=product.id, target=target_price)
            return alert.id

    async def get_user_alerts(self, user_id: int) -> list[dict]:
        async with get_db_session() as session:
            result = await session.execute(
                select(Alert)
                .where(Alert.user_id == user_id, Alert.is_active == True)
                .options(selectinload(Alert.product))
                .order_by(Alert.created_at.desc())
            )
            alerts = result.scalars().all()
            return [
                {
                    "alert_id": a.id,
                    "product_id": a.product.id,
                    "title": a.product.title,
                    "current_price": a.product.price,
                    "target_price": a.target_price,
                    "currency": a.currency,
                    "store": a.product.store,
                    "product_url": a.product.product_url,
                    "alert_type": a.alert_type.value,
                    "created_at": a.created_at.isoformat(),
                }
                for a in alerts
            ]

    async def get_all_active_alerts(self) -> list[Alert]:
        async with get_db_session() as session:
            result = await session.execute(
                select(Alert)
                .where(Alert.is_active == True)
                .options(selectinload(Alert.product), selectinload(Alert.user))
            )
            return result.scalars().all()

    async def deactivate_alert(self, alert_id: int) -> None:
        async with get_db_session() as session:
            result = await session.execute(select(Alert).where(Alert.id == alert_id))
            alert = result.scalar_one_or_none()
            if alert:
                alert.is_active = False
                from datetime import datetime
                alert.triggered_at = datetime.utcnow()

    async def remove_alert(self, user_id: int, alert_id: int) -> bool:
        async with get_db_session() as session:
            result = await session.execute(
                delete(Alert).where(
                    Alert.id == alert_id,
                    Alert.user_id == user_id,
                )
            )
            return result.rowcount > 0

    async def get_stats(self) -> dict:
        from sqlalchemy import func
        async with get_db_session() as session:
            total = (await session.execute(
                select(func.count(Alert.id)).where(Alert.is_active == True)
            )).scalar_one()
            favorites = (await session.execute(
                select(func.count(Favorite.id))
            )).scalar_one()
            return {
                "total_alerts": total,
                "total_favorites": favorites,
            }


favorites_service = FavoritesService()
watchlist_service = WatchlistService()
alert_service = AlertService()
