"""Initial migration — create all tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enums ---
    language_code = postgresql.ENUM("uz", "ru", "en", name="languagecode")
    language_code.create(op.get_bind(), checkfirst=True)

    alert_type = postgresql.ENUM("instant", "daily", name="alerttype")
    alert_type.create(op.get_bind(), checkfirst=True)

    admin_action_type = postgresql.ENUM("broadcast", "ban", "unban", "view_stats", name="adminactiontype")
    admin_action_type.create(op.get_bind(), checkfirst=True)

    # --- Users ---
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("first_name", sa.String(128), nullable=False),
        sa.Column("last_name", sa.String(128), nullable=True),
        sa.Column("language", sa.Enum("uz", "ru", "en", name="languagecode"), nullable=False, server_default="uz"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_active_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index("ix_users_is_banned", "users", ["is_banned"])

    # --- Products ---
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("external_id", sa.String(256), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(16), nullable=False, server_default="UZS"),
        sa.Column("availability", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("product_url", sa.Text(), nullable=False),
        sa.Column("store", sa.String(64), nullable=False),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("brand", sa.String(128), nullable=True),
        sa.Column("specifications", sa.Text(), nullable=True),
        sa.Column("last_scraped_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_url", "store", name="uq_product_url_store"),
    )
    op.create_index("ix_products_store", "products", ["store"])
    op.create_index("ix_products_title", "products", ["title"])

    # --- Favorites ---
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_favorite_user_product"),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])

    # --- Watchlists ---
    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_watchlist_user_product"),
    )
    op.create_index("ix_watchlists_user_id", "watchlists", ["user_id"])

    # --- Alerts ---
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("target_price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(16), nullable=False, server_default="UZS"),
        sa.Column("alert_type", sa.Enum("instant", "daily", name="alerttype"), nullable=False, server_default="instant"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("triggered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_user_id", "alerts", ["user_id"])
    op.create_index("ix_alerts_is_active", "alerts", ["is_active"])

    # --- Search History ---
    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("query", sa.String(512), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("search_type", sa.String(32), nullable=False, server_default="text"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_history_user_id", "search_history", ["user_id"])
    op.create_index("ix_search_history_query", "search_history", ["query"])
    op.create_index("ix_search_history_created_at", "search_history", ["created_at"])

    # --- Search Cache ---
    op.create_table(
        "search_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cache_key", sa.String(256), nullable=False, unique=True),
        sa.Column("query", sa.String(512), nullable=False),
        sa.Column("results", sa.Text(), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_cache_cache_key", "search_cache", ["cache_key"])

    # --- Banned Users ---
    op.create_table(
        "banned_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("banned_by", sa.BigInteger(), nullable=False),
        sa.Column("banned_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("unbanned_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_banned_users_is_active", "banned_users", ["is_active"])

    # --- Admin Logs ---
    op.create_table(
        "admin_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("admin_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.Enum("broadcast", "ban", "unban", "view_stats", name="adminactiontype"), nullable=False),
        sa.Column("target_user_id", sa.BigInteger(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_logs_admin_id", "admin_logs", ["admin_id"])
    op.create_index("ix_admin_logs_created_at", "admin_logs", ["created_at"])

    # --- Analytics ---
    op.create_table(
        "analytics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("total_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_searches", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_alerts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_favorites", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analytics_date", "analytics", ["date"])

    # --- Price History ---
    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(16), nullable=False, server_default="UZS"),
        sa.Column("recorded_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_price_history_product_id", "price_history", ["product_id"])
    op.create_index("ix_price_history_recorded_at", "price_history", ["recorded_at"])


def downgrade() -> None:
    op.drop_table("price_history")
    op.drop_table("analytics")
    op.drop_table("admin_logs")
    op.drop_table("banned_users")
    op.drop_table("search_cache")
    op.drop_table("search_history")
    op.drop_table("alerts")
    op.drop_table("watchlists")
    op.drop_table("favorites")
    op.drop_table("products")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS adminactiontype")
    op.execute("DROP TYPE IF EXISTS alerttype")
    op.execute("DROP TYPE IF EXISTS languagecode")
