"""
Halol Crypto AI - Web Server
Serves the Telegram Mini App and handles webhook mode.
"""

import asyncio
import logging
from pathlib import Path

from aiohttp import web

from config import WEBAPP_HOST, WEBAPP_PORT, BOT_TOKEN, WEBHOOK_PATH, WEBHOOK_URL
from database import init_db
from scanner import close_session

logger = logging.getLogger(__name__)

WEBAPP_DIR = Path(__file__).parent / "webapp"


# ─── Routes ───────────────────────────────────────────────────────────────────

async def index(request: web.Request) -> web.Response:
    """Serve the Mini App."""
    index_file = WEBAPP_DIR / "index.html"
    return web.FileResponse(index_file)


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "Halol Crypto AI"})


async def webhook(request: web.Request) -> web.Response:
    """Handle Telegram webhook updates."""
    try:
        from telegram import Update
        app = request.app["bot_app"]
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
        return web.Response(text="OK")
    except Exception as e:
        logger.error("Webhook error: %s", e)
        return web.Response(status=500)


# ─── App Factory ──────────────────────────────────────────────────────────────

async def create_web_app(bot_app=None) -> web.Application:
    app = web.Application()

    # Static files
    static_dir = WEBAPP_DIR / "static"
    if static_dir.exists():
        app.router.add_static("/static", static_dir)

    # Routes
    app.router.add_get("/",        index)
    app.router.add_get("/health",  health)
    app.router.add_get("/webapp",  index)

    if bot_app and WEBHOOK_URL:
        app["bot_app"] = bot_app
        app.router.add_post(WEBHOOK_PATH, webhook)
        logger.info("Webhook mode enabled at %s", WEBHOOK_PATH)

    # Startup/shutdown
    async def on_startup(app):
        await init_db()
        logger.info("Web server started on %s:%s", WEBAPP_HOST, WEBAPP_PORT)

    async def on_shutdown(app):
        await close_session()
        logger.info("Web server shutting down")

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


async def run_webapp(bot_app=None):
    app = await create_web_app(bot_app)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()
    logger.info("🌐 Mini App running at http://%s:%s", WEBAPP_HOST, WEBAPP_PORT)
    return runner


# ─── Entry point (standalone) ─────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def main():
        runner = await run_webapp()
        try:
            await asyncio.Event().wait()
        finally:
            await runner.cleanup()

    asyncio.run(main())
