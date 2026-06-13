"""
Background price alert checker.
Runs periodically, checks product prices, fires alerts when target is reached.
"""
from __future__ import annotations

import asyncio
from datetime import datetime

from aiogram import Bot

from services.favorites import alert_service
from providers import registry
from core.config import settings
from core.logging_config import get_logger
from utils.i18n import t

logger = get_logger(__name__)


async def check_alerts(bot: Bot) -> None:
    """
    Main alert checking loop.
    Fetches all active alerts, re-scrapes each product price,
    fires Telegram notifications when target is hit.
    """
    logger.info("alert_check_start")

    try:
        alerts = await alert_service.get_all_active_alerts()
        if not alerts:
            logger.info("alert_check_no_alerts")
            return

        logger.info("alert_check_processing", count=len(alerts))

        # Process in batches to avoid hammering providers
        batch_size = settings.ALERT_BATCH_SIZE
        for i in range(0, len(alerts), batch_size):
            batch = alerts[i:i + batch_size]
            await asyncio.gather(
                *[_process_alert(alert, bot) for alert in batch],
                return_exceptions=True,
            )
            await asyncio.sleep(2)  # Brief pause between batches

    except Exception as e:
        logger.error("alert_check_error", error=str(e))


async def _process_alert(alert, bot: Bot) -> None:
    """Process a single alert: re-scrape price, compare, notify."""
    try:
        product = alert.product
        if not product:
            return

        # Re-fetch current price
        current_product = await registry.get_product_by_url(product.product_url)
        if not current_product:
            return

        current_price = current_product.price
        if current_price is None:
            return

        # Update product price in DB
        from database.db import get_db_session
        from database.models import PriceHistory
        from sqlalchemy import update

        async with get_db_session() as session:
            from sqlalchemy import update
            from database.models import Product
            await session.execute(
                update(Product)
                .where(Product.id == product.id)
                .values(price=current_price, last_scraped_at=datetime.utcnow())
            )
            session.add(PriceHistory(
                product_id=product.id,
                price=current_price,
                currency=product.currency,
            ))

        # Check if target price reached
        if current_price <= alert.target_price:
            await _fire_alert(alert, current_price, bot)

    except Exception as e:
        logger.error("process_alert_error", alert_id=alert.id, error=str(e))


async def _fire_alert(alert, current_price: float, bot: Bot) -> None:
    """Send Telegram notification and deactivate alert."""
    try:
        user = alert.user
        product = alert.product
        lang = user.language.value if user else "uz"

        text = t(
            "alert_triggered",
            lang,
            product=product.title[:60],
            price=f"{current_price:,.0f} {product.currency}",
            target=f"{alert.target_price:,.0f} {alert.currency}",
        )

        await bot.send_message(
            chat_id=user.id,
            text=text,
            parse_mode="HTML",
        )

        # Deactivate alert after firing
        await alert_service.deactivate_alert(alert.id)

        logger.info(
            "alert_fired",
            alert_id=alert.id,
            user_id=user.id,
            current_price=current_price,
            target=alert.target_price,
        )

    except Exception as e:
        logger.error("fire_alert_error", alert_id=alert.id, error=str(e))


async def run_alert_scheduler(bot: Bot) -> None:
    """Infinite loop that runs alert checks at configured intervals."""
    logger.info("alert_scheduler_started", interval=settings.PRICE_CHECK_INTERVAL)
    while True:
        try:
            await check_alerts(bot)
        except Exception as e:
            logger.error("alert_scheduler_error", error=str(e))
        await asyncio.sleep(settings.PRICE_CHECK_INTERVAL)
