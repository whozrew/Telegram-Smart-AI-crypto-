"""
Provider registry.
Manages all marketplace providers, handles URL routing, and fan-out searches.
"""
from __future__ import annotations

import asyncio
from typing import Optional

from providers.base import BaseProvider, ProductResult
from providers.uzum import UzumProvider
from providers.olx import OlxProvider
from providers.asaxiy import AsaxiyProvider
from providers.uzbek_stores import (
    MediaParkProvider,
    TexnomartProvider,
    IdeaProvider,
    GoodzoneProvider,
    ZoodmallProvider,
)
from providers.global_stores import (
    AliExpressProvider,
    AmazonProvider,
    EbayProvider,
    TemuProvider,
    WildberriesProvider,
)
from core.logging_config import get_logger

logger = get_logger(__name__)


class ProviderRegistry:
    """Central registry for all marketplace providers."""

    def __init__(self):
        self._providers: list[BaseProvider] = []
        self._register_defaults()

    def _register_defaults(self):
        # Uzbek stores
        self.register(UzumProvider())
        self.register(OlxProvider())
        self.register(AsaxiyProvider())
        self.register(MediaParkProvider())
        self.register(TexnomartProvider())
        self.register(IdeaProvider())
        self.register(GoodzoneProvider())
        self.register(ZoodmallProvider())
        # Global stores
        self.register(AliExpressProvider())
        self.register(AmazonProvider())
        self.register(EbayProvider())
        self.register(TemuProvider())
        self.register(WildberriesProvider())

    def register(self, provider: BaseProvider) -> None:
        self._providers.append(provider)
        logger.info("provider_registered", name=provider.name)

    @property
    def uzbek_providers(self) -> list[BaseProvider]:
        return [p for p in self._providers if p.is_uzbek]

    @property
    def global_providers(self) -> list[BaseProvider]:
        return [p for p in self._providers if not p.is_uzbek]

    @property
    def all_providers(self) -> list[BaseProvider]:
        return self._providers

    async def find_provider_for_url(self, url: str) -> Optional[BaseProvider]:
        """Find the provider that handles a given URL."""
        for provider in self._providers:
            if await provider.supports_url(url):
                return provider
        return None

    async def search_all(
        self,
        query: str,
        max_results_per_provider: int = 5,
        timeout: float = 15.0,
        uzbek_only: bool = False,
        global_only: bool = False,
    ) -> list[ProductResult]:
        """
        Fan-out search across all providers concurrently.
        Returns combined and deduplicated results.
        """
        providers = self._providers
        if uzbek_only:
            providers = self.uzbek_providers
        elif global_only:
            providers = self.global_providers

        tasks = [
            asyncio.create_task(
                self._safe_search(provider, query, max_results_per_provider),
                name=f"search_{provider.name}",
            )
            for provider in providers
        ]

        results: list[ProductResult] = []
        done, pending = await asyncio.wait(tasks, timeout=timeout)

        for task in pending:
            task.cancel()

        for task in done:
            try:
                task_results = task.result()
                if task_results:
                    results.extend(task_results)
            except Exception as e:
                logger.warning("provider_task_error", error=str(e))

        # Sort: available first, then by price
        results.sort(key=lambda r: (not r.availability, r.price or float("inf")))
        return results

    async def _safe_search(
        self, provider: BaseProvider, query: str, max_results: int
    ) -> list[ProductResult]:
        """Wrap provider search with error handling."""
        try:
            results = await provider.search(query, max_results)
            logger.info(
                "provider_search_done",
                provider=provider.name,
                query=query,
                count=len(results),
            )
            return results
        except Exception as e:
            logger.error(
                "provider_search_error",
                provider=provider.name,
                query=query,
                error=str(e),
            )
            return []

    async def get_product_by_url(self, url: str) -> Optional[ProductResult]:
        """Fetch a product by URL, routing to the correct provider."""
        provider = await self.find_provider_for_url(url)
        if not provider:
            logger.warning("no_provider_for_url", url=url)
            return None
        try:
            return await provider.get_product(url)
        except Exception as e:
            logger.error("get_product_error", url=url, error=str(e))
            return None


# Singleton
registry = ProviderRegistry()
