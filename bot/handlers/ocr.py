"""
OCR handler.
Processes photo messages, extracts product name via Gemini Vision,
then runs a search automatically.
"""
from __future__ import annotations

import io

from aiogram import Router, F, Bot
from aiogram.types import Message

from services.gemini import gemini_service
from services.search import search_service
from services.session import create_search_session
from services.user import user_service
from bot.handlers.search import _send_product_card
from utils.i18n import t
from core.logging_config import get_logger

logger = get_logger(__name__)
router = Router(name="ocr")


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot, db_user, user_lang: str):
    """Handle photo messages for OCR product detection."""
    processing_msg = await message.answer(t("ocr_processing", user_lang))

    try:
        # Get the highest-resolution photo
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)

        # Download file bytes
        file_bytes = io.BytesIO()
        await bot.download_file(file_info.file_path, destination=file_bytes)
        image_data = file_bytes.getvalue()

        # Detect MIME type (Telegram usually sends JPEG)
        mime_type = "image/jpeg"

        # Extract product name via Gemini Vision
        product_name = await gemini_service.extract_product_from_image(
            image_bytes=image_data,
            mime_type=mime_type,
        )

        await processing_msg.delete()

        if not product_name:
            await message.answer(t("ocr_failed", user_lang))
            return

        # Show what was found
        await message.answer(
            t("ocr_found", user_lang, product=product_name),
            parse_mode="HTML",
        )

        # Run search
        searching_msg = await message.answer(t("searching", user_lang))

        user_id = db_user.id if db_user else message.from_user.id
        result = await search_service.search_by_text(product_name, user_id)

        await searching_msg.delete()
        await user_service.record_search(user_id, product_name, result.get("total", 0), "image")

        all_results = result.get("all", [])
        if not all_results:
            await message.answer(t("search_no_results", user_lang, query=product_name), parse_mode="HTML")
            return

        combined = result.get("exact", []) + result.get("similar", [])
        if not combined:
            combined = all_results

        session_id = await create_search_session(user_id, combined, product_name)

        header = t("search_results_header", user_lang, query=product_name, count=len(combined))
        await message.answer(header, parse_mode="HTML")

        await _send_product_card(
            message,
            combined[0],
            index=0,
            total=len(combined),
            session_id=session_id,
            lang=user_lang,
            user_id=user_id,
        )

    except Exception as e:
        logger.error("ocr_handler_error", error=str(e))
        try:
            await processing_msg.delete()
        except Exception:
            pass
        await message.answer(t("error_generic", user_lang))
