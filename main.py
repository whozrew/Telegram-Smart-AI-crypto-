"""
Halol Crypto AI - Main Entry Point
Runs both the Telegram bot and the Mini App web server.

Modes:
  python main.py           → polling + web server (default, local/VPS)
  python main.py --webhook → webhook mode (Railway/Render)
  python main.py --webonly → web server only (for testing UI)
"""

import asyncio
import logging
import sys
from pathlib import Path

# ─── Logging setup ────────────────────────────────────────────────────────────

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "halol.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ─── Polling mode (default) ───────────────────────────────────────────────────

async def run_polling():
    """Run bot in polling mode + web server concurrently."""
    from database import init_db
    from bot import build_app, background_scanner
    from webapp_server import run_webapp

    await init_db()

    bot_app = build_app()
    await bot_app.initialize()
    await bot_app.start()

    # Start background alert scanner
    scanner_task = asyncio.create_task(background_scanner(bot_app))

    # Start web server for Mini App
    web_runner = await run_webapp()

    logger.info("🌟 Halol Crypto AI is LIVE!")
    logger.info("📱 Bot: polling mode")
    logger.info("🌐 Mini App: http://0.0.0.0:8080")

    try:
        await bot_app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()   # Run forever
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
    finally:
        scanner_task.cancel()
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
        await web_runner.cleanup()


# ─── Webhook mode (Railway / Render) ─────────────────────────────────────────

async def run_webhook():
    """Run bot in webhook mode (production hosting)."""
    from config import WEBHOOK_URL, WEBHOOK_PATH
    from database import init_db
    from bot import build_app, background_scanner
    from webapp_server import run_webapp

    if not WEBHOOK_URL:
        logger.error("WEBHOOK_URL must be set for webhook mode!")
        sys.exit(1)

    await init_db()

    bot_app = build_app()
    await bot_app.initialize()
    await bot_app.start()

    # Set webhook
    webhook_full = f"{WEBHOOK_URL.rstrip('/')}{WEBHOOK_PATH}"
    await bot_app.bot.set_webhook(webhook_full)
    logger.info("✅ Webhook set to: %s", webhook_full)

    # Background scanner
    scanner_task = asyncio.create_task(background_scanner(bot_app))

    # Web server handles both Mini App + webhook
    web_runner = await run_webapp(bot_app)

    logger.info("🌟 Halol Crypto AI is LIVE (webhook mode)!")

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
    finally:
        scanner_task.cancel()
        await bot_app.bot.delete_webhook()
        await bot_app.stop()
        await bot_app.shutdown()
        await web_runner.cleanup()


# ─── Web only (UI testing) ────────────────────────────────────────────────────

async def run_webonly():
    """Run only the web server — useful for UI development."""
    from webapp_server import run_webapp
    runner = await run_webapp()
    logger.info("🌐 Mini App running at http://0.0.0.0:8080")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await runner.cleanup()


# ─── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""

    if mode == "--webhook":
        asyncio.run(run_webhook())
    elif mode == "--webonly":
        asyncio.run(run_webonly())
    else:
        asyncio.run(run_polling())
