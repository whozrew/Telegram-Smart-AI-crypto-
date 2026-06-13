"""
Uzum.uz marketplace provider.
Uses Uzum's public search API.
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import quote

from providers.base import BaseProvider, ProductResult
from utils.http_client import fetch_json
from core.logging_config import get_logger

logger = get_logger(__name__)


class UzumProvider(BaseProvider):
    name = "uzum"
    display_name = "Uzum"
    base_url = "https://uzum.uz"
    logo_url = "https://uzum.uz/favicon.ico"
    is_uzbek = True

    SEARCH_API = "https://api.uzum.uz/api/v2/search"
    PRODUCT_API = "https://api.uzum.uz/api/v2/product/{product_id}"

    async def search(self, query: str, max_results: int = 10) -> list[ProductResult]:
        results = []
        try:
            params = {
                "categoryId": "1",
                "query": query,
                "sortBy": "RELEVANCE",
                "size": min(max_results, 40),
                "page": 0,
            }
            headers = {
                "x-iid": "uzum.uz",
                "Authorization": "Basic dXp1bS51emVyOnV6dW0udXplcg==",
            }
            data = await fetch_json(self.SEARCH_API, params=params, headers=headers)

            if not data:
                return results

            products = (
                data.get("payload", {})
                .get("products", [])
            )
            if not products:
                products = data.get("products", [])

            for item in products[:max_results]:
                try:
                    price_raw = item.get("sellPrice") or item.get("minSellPrice") or 0
                    price = float(price_raw) / 100 if price_raw else None  # Uzum stores in tiyin

                    product_id = item.get("productId") or item.get("id")
                    url = f"{self.base_url}/product/{product_id}" if product_id else self.base_url

                    # Image
                    photos = item.get("photos") or item.get("images") or []
                    image_url = None
                    if photos:
                        first_photo = photos[0] if isinstance(photos[0], str) else photos[0].get("photo") or photos[0].get("url")
                        if first_photo:
                            image_url = f"https://cdn.uzum.uz/{first_photo}" if not first_photo.startswith("http") else first_photo

                    rating = item.get("rating") or item.get("averageRating")
                    if rating:
                        rating = float(rating)

                    results.append(ProductResult(
                        title=item.get("title") or item.get("name") or "Unknown",
                        price=price,
                        currency="UZS",
                        availability=item.get("sellable", True),
                        rating=rating,
                        review_count=int(item.get("reviewsAmount") or item.get("totalRatings") or 0),
                        image_url=image_url,
                        product_url=url,
                        store=self.display_name,
                        external_id=str(product_id),
                        category=item.get("categoryTitle"),
                    ))
                except Exception as e:
                    logger.warning("uzum_parse_error", error=str(e))
                    continue

        except Exception as e:
            logger.error("uzum_search_error", query=query, error=str(e))

        return results

    async def get_product(self, url: str) -> Optional[ProductResult]:
        try:
            # Extract product ID from URL
            parts = url.rstrip("/").split("/")
            product_id = None
            for i, part in enumerate(parts):
                if part == "product" and i + 1 < len(parts):
                    product_id = parts[i + 1]
                    break

            if not product_id:
                return None

            api_url = self.PRODUCT_API.format(product_id=product_id)
            headers = {
                "x-iid": "uzum.uz",
                "Authorization": "Basic dXp1bS51emVyOnV6dW0udXplcg==",
            }
            data = await fetch_json(api_url, headers=headers)
            if not data:
                return None

            payload = data.get("payload") or data

            price_raw = payload.get("minSellPrice") or payload.get("sellPrice") or 0
            price = float(price_raw) / 100 if price_raw else None

            photos = payload.get("photos") or []
            image_url = None
            if photos:
                p = photos[0]
                photo_path = p if isinstance(p, str) else p.get("photo") or p.get("url")
                if photo_path:
                    image_url = f"https://cdn.uzum.uz/{photo_path}" if not photo_path.startswith("http") else photo_path

            rating = payload.get("rating") or payload.get("averageRating")

            return ProductResult(
                title=payload.get("title") or payload.get("name") or "Unknown",
                price=price,
                currency="UZS",
                availability=payload.get("sellable", True),
                rating=float(rating) if rating else None,
                review_count=int(payload.get("reviewsAmount") or 0),
                image_url=image_url,
                product_url=url,
                store=self.display_name,
                external_id=str(product_id),
                description=payload.get("description"),
            )
        except Exception as e:
            logger.error("uzum_get_product_error", url=url, error=str(e))
            return None

    async def supports_url(self, url: str) -> bool:
        return "uzum.uz" in url
