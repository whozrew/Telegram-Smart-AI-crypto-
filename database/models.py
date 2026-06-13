"""
All ORM models for the Bozor Narxlari bot.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base


class LanguageCode(str, enum.Enum):
    UZ = "uz"
    RU = "ru"
    EN = "en"


class AlertType(str, enum.Enum):
    INSTANT = "instant"
    DAILY = "daily"


class AdminActionType(str, enum.Enum):
    BROADCAST = "broadcast"
    BAN = "ban"
    UNBAN = "unban"
    VIEW_STATS = "view_stats"


# ─────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user id
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128))
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    language: Mapped[LanguageCode] = mapped_column(
        Enum(LanguageCode), default=LanguageCode.UZ, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    favorites: Mapped[list["Favorite"]] = relationship(
        "Favorite", back_populates="user", lazy="select"
    )
    watchlist: Mapped[list["Watchlist"]] = relationship(
        "Watchlist", back_populates="user", lazy="select"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="user", lazy="select"
    )
    search_history: Mapped[list["SearchHistory"]] = relationship(
        "SearchHistory", back_populates="user", lazy="select"
    )

    __table_args__ = (
        Index("ix_users_is_active", "is_active"),
        Index("ix_users_is_banned", "is_banned"),
    )


# ─────────────────────────────────────────────
# Products
# ─────────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(16), default="UZS")
    availability: Mapped[bool] = mapped_column(Boolean, default=True)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_url: Mapped[str] = mapped_column(Text)
    store: Mapped[str] = mapped_column(String(64))
    category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    specifications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    favorites: Mapped[list["Favorite"]] = relationship(
        "Favorite", back_populates="product", lazy="select"
    )
    watchlists: Mapped[list["Watchlist"]] = relationship(
        "Watchlist", back_populates="product", lazy="select"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="product", lazy="select"
    )

    __table_args__ = (
        Index("ix_products_store", "store"),
        Index("ix_products_title", "title"),
        UniqueConstraint("product_url", "store", name="uq_product_url_store"),
    )


# ─────────────────────────────────────────────
# Favorites
# ─────────────────────────────────────────────

class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="favorites")
    product: Mapped["Product"] = relationship("Product", back_populates="favorites")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_favorite_user_product"),
        Index("ix_favorites_user_id", "user_id"),
    )


# ─────────────────────────────────────────────
# Watchlist
# ─────────────────────────────────────────────

class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="watchlist")
    product: Mapped["Product"] = relationship("Product", back_populates="watchlists")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_watchlist_user_product"),
        Index("ix_watchlists_user_id", "user_id"),
    )


# ─────────────────────────────────────────────
# Alerts
# ─────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    target_price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(16), default="UZS")
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType), default=AlertType.INSTANT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="alerts")
    product: Mapped["Product"] = relationship("Product", back_populates="alerts")

    __table_args__ = (
        Index("ix_alerts_user_id", "user_id"),
        Index("ix_alerts_is_active", "is_active"),
    )


# ─────────────────────────────────────────────
# Search History
# ─────────────────────────────────────────────

class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    query: Mapped[str] = mapped_column(String(512))
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    search_type: Mapped[str] = mapped_column(String(32), default="text")  # text, url, image
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="search_history")

    __table_args__ = (
        Index("ix_search_history_user_id", "user_id"),
        Index("ix_search_history_query", "query"),
        Index("ix_search_history_created_at", "created_at"),
    )


# ─────────────────────────────────────────────
# Search Cache
# ─────────────────────────────────────────────

class SearchCache(Base):
    __tablename__ = "search_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cache_key: Mapped[str] = mapped_column(String(256), unique=True)
    query: Mapped[str] = mapped_column(String(512))
    results: Mapped[str] = mapped_column(Text)  # JSON
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (Index("ix_search_cache_cache_key", "cache_key"),)


# ─────────────────────────────────────────────
# Banned Users
# ─────────────────────────────────────────────

class BannedUser(Base):
    __tablename__ = "banned_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    banned_by: Mapped[int] = mapped_column(BigInteger)
    banned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    unbanned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (Index("ix_banned_users_is_active", "is_active"),)


# ─────────────────────────────────────────────
# Admin Logs
# ─────────────────────────────────────────────

class AdminLog(Base):
    __tablename__ = "admin_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[AdminActionType] = mapped_column(Enum(AdminActionType))
    target_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_admin_logs_admin_id", "admin_id"),
        Index("ix_admin_logs_created_at", "created_at"),
    )


# ─────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────

class Analytics(Base):
    __tablename__ = "analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime)
    total_users: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)
    total_searches: Mapped[int] = mapped_column(Integer, default=0)
    total_alerts: Mapped[int] = mapped_column(Integer, default=0)
    total_favorites: Mapped[int] = mapped_column(Integer, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (Index("ix_analytics_date", "date"),)


# ─────────────────────────────────────────────
# Price History (for tracking)
# ─────────────────────────────────────────────

class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(16), default="UZS")
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_price_history_product_id", "product_id"),
        Index("ix_price_history_recorded_at", "recorded_at"),
    )
