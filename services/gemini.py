"""
Google Gemini AI service.
Provides AI advice for products and OCR text extraction from images.
"""
from __future__ import annotations

import base64
import json
from typing import Optional

import aiohttp

from core.config import settings
from core.logging_config import get_logger

logger = get_logger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = "gemini-1.5-flash"  # Free tier model
GEMINI_VISION_MODEL = "gemini-1.5-flash"


AI_ADVICE_PROMPT = """
You are a product expert and shopping advisor. Analyze the following product and provide:

Product: {product_title}
Price: {price}
Store: {store}
Rating: {rating}

Please provide a detailed analysis in {language} with these sections:

**📝 Product Summary**
Brief overview of the product.

**✅ Pros**
- List main advantages

**❌ Cons**
- List main disadvantages

**💰 Value for Money**
Assessment of price vs quality.

**🔄 Alternatives**
2-3 alternative products to consider.

**🎯 Recommendation**
Should the user buy this product? Clear yes/no with reasoning.

Keep the response concise and practical. Language: {language}.
"""

OCR_PROMPT = """
Look at this image carefully. It appears to be a screenshot of a product, shopping page, or product listing.

Extract the main product name and model from this image.

Respond ONLY with a JSON object like this:
{"product_name": "exact product name here", "confidence": 0.9}

If you cannot identify a product, respond:
{"product_name": null, "confidence": 0.0}

Do not include any other text.
"""


class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_ai_advice(
        self,
        product_title: str,
        price: str,
        store: str,
        rating: str,
        language: str = "uz",
    ) -> Optional[str]:
        """Get AI-powered product advice."""
        lang_name = {"uz": "Uzbek", "ru": "Russian", "en": "English"}.get(language, "English")

        prompt = AI_ADVICE_PROMPT.format(
            product_title=product_title,
            price=price,
            store=store,
            rating=rating,
            language=lang_name,
        )

        return await self._generate_text(prompt)

    async def extract_product_from_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> Optional[str]:
        """Extract product name from image using Gemini Vision."""
        try:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": b64_image,
                                }
                            },
                            {"text": OCR_PROMPT},
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 200,
                },
            }

            url = (
                f"{GEMINI_API_BASE}/models/{GEMINI_VISION_MODEL}"
                f":generateContent?key={self.api_key}"
            )
            session = await self._get_session()
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error("gemini_vision_error", status=resp.status, body=error_text[:300])
                    return None

                data = await resp.json()
                text = self._extract_text(data)
                if not text:
                    return None

                # Parse JSON response
                text = text.strip()
                # Strip possible markdown code blocks
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                text = text.strip()

                parsed = json.loads(text)
                product_name = parsed.get("product_name")
                confidence = parsed.get("confidence", 0.0)

                if product_name and confidence >= 0.3:
                    return product_name

                return None

        except json.JSONDecodeError:
            logger.warning("gemini_ocr_json_error")
            return None
        except Exception as e:
            logger.error("gemini_ocr_error", error=str(e))
            return None

    async def _generate_text(self, prompt: str) -> Optional[str]:
        """Call Gemini text generation API."""
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1000,
                    "topP": 0.9,
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                    },
                ],
            }

            url = (
                f"{GEMINI_API_BASE}/models/{GEMINI_MODEL}"
                f":generateContent?key={self.api_key}"
            )
            session = await self._get_session()
            async with session.post(url, json=payload) as resp:
                if resp.status == 429:
                    logger.warning("gemini_rate_limited")
                    return "⚠️ AI service is currently busy. Please try again in a moment."

                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error("gemini_api_error", status=resp.status, body=error_text[:300])
                    return None

                data = await resp.json()
                return self._extract_text(data)

        except aiohttp.ClientError as e:
            logger.error("gemini_network_error", error=str(e))
            return None
        except Exception as e:
            logger.error("gemini_error", error=str(e))
            return None

    def _extract_text(self, data: dict) -> Optional[str]:
        """Extract text from Gemini API response."""
        try:
            candidates = data.get("candidates") or []
            if not candidates:
                return None
            content = candidates[0].get("content") or {}
            parts = content.get("parts") or []
            if not parts:
                return None
            return parts[0].get("text")
        except Exception:
            return None

    async def compare_products(
        self,
        products: list[dict],
        language: str = "uz",
    ) -> Optional[str]:
        """AI-powered product comparison."""
        lang_name = {"uz": "Uzbek", "ru": "Russian", "en": "English"}.get(language, "English")

        product_list = "\n".join(
            f"{i+1}. {p['title']} | {p.get('price', 'N/A')} | {p.get('store', 'N/A')} | Rating: {p.get('rating', 'N/A')}"
            for i, p in enumerate(products)
        )

        prompt = f"""
Compare these products and give a recommendation in {lang_name}:

{product_list}

Provide:
1. Quick comparison table (price, quality, availability)
2. Best value choice
3. Premium choice
4. Budget choice
5. Final recommendation

Be concise and practical.
"""
        return await self._generate_text(prompt)


# Singleton
gemini_service = GeminiService()
