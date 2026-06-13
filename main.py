"""
Main bot application.
Entry point — sets up all components and starts polling.
"""
from __future__ import annotations

import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from core.config import settings
from core.logging_config import setup_logging, get_logger

# Setup logging before anything else
setup_logging()
logger = get_logger(__name__)


async def on_startup(bot: Bot) -> None:
    """Called when bot starts."""
    logger.info("bot_startup", environment=settings.ENVIRONMENT)

    # Initialize database
    from database.db import init_db
    await init_db()
    logger.info("database_ready")

    # Test Redis
    from services.cache import get_redis
    redis = await get_redis()
    await redis.ping()
    logger.info("redis_ready")

    # Start background alert scheduler
    from services.scheduler import run_alert_scheduler
    asyncio.create_task(run_alert_scheduler(bot), name="alert_scheduler")
    logger.info("scheduler_started")

    # Set bot commands
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="Start / Restart"),
        BotCommand(command="search", description="Search products"),
        BotCommand(command="favorites", description="Saved products"),
        BotCommand(command="watchlist", description="Watchlist"),
        BotCommand(command="alerts", description="Price alerts"),
        BotCommand(command="language", description="Change language"),
        BotCommand(command="help", description="Help"),
    ]
    await bot.set_my_commands(commands)
    logger.info("bot_commands_set")


async def on_shutdown(bot: Bot) -> None:
    """Called when bot stops."""
    logger.info("bot_shutdown")
    from database.db import close_db
    from services.cache import close_redis
    from services.gemini import gemini_service
    await close_db()
    await close_redis()
    await gemini_service.close()


def create_dispatcher() -> Dispatcher:
    """Create and configure the Aiogram dispatcher."""
    # Redis FSM storage
    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = Dispatcher(storage=storage)

    # Register middlewares (order matters!)
    from bot.middlewares import (
        UserContextMiddleware,
        BanCheckMiddleware,
        AntiSpamMiddleware,
    )
    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())
    dp.message.middleware(BanCheckMiddleware())
    dp.message.middleware(AntiSpamMiddleware())

    # Register routers
    from bot.handlers.start import router as start_router
    from bot.handlers.search import router as search_router
    from bot.handlers.ocr import router as ocr_router
    from bot.handlers.favorites import router as favorites_router
    from bot.handlers.watchlist import router as watchlist_router
    from bot.handlers.alerts import router as alerts_router
    from bot.handlers.admin import router as admin_router

    dp.include_routers(
        start_router,
        ocr_router,       # OCR before search (photo handler)
        admin_router,     # Admin before general message handler
        favorites_router,
        watchlist_router,
        alerts_router,
        search_router,    # Search last (catches all remaining text)
    )

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    return dp


async def main() -> None:
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = create_dispatcher()

    logger.info("starting_polling")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("bot_stopped_by_user")
        sys.exit(0)
