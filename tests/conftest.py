import logging
from collections.abc import Generator
from typing import Any

import pytest
import pytest_asyncio
from randouyin.adapters.playwright_scraper import PlaywrightScraper
from randouyin.config.settings import get_settings
from randouyin.ports.base_scraper import BaseScraper

logger = logging.getLogger("test")


@pytest_asyncio.fixture
async def scraper() -> BaseScraper:
    logger.info("Setting up scraper test client")
    return PlaywrightScraper()


@pytest.fixture
def get_clean_settings_between_tests() -> Generator[None, Any, Any]:
    yield
    get_settings.cache_clear()
