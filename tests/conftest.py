import json
import logging
from collections.abc import Generator
from typing import Any

import pytest
import pytest_asyncio
from randouyin.adapters.beautiful_soup_parser import BeautifulSoupParser
from randouyin.adapters.playwright_scraper import PlaywrightScraper
from randouyin.config.settings import get_settings
from randouyin.ports.base_parser import BaseParser
from randouyin.ports.base_scraper import BaseScraper

logger = logging.getLogger("test")


@pytest_asyncio.fixture
async def scraper() -> BaseScraper:
    logger.info("Setting up scraper test client")
    return PlaywrightScraper()


@pytest_asyncio.fixture
async def parser() -> BaseParser:
    logger.info("Setting up test parser")
    return BeautifulSoupParser()


@pytest_asyncio.fixture
async def search_video_card_html() -> tuple[str, dict]:
    """Get one search result video card for parsing tests

    Returns:
        tuple[str, dict]:
        str: HTML string of search result video card
        dict: expected parsing result
    """
    with open("tests/example/search_video_card/input.html") as f:
        html = f.read()
    with open("tests/example/search_video_card/result.json") as f:
        result = json.load(f)
    return html, result


@pytest.fixture
def get_clean_settings_between_tests() -> Generator[None, Any, Any]:
    yield
    get_settings.cache_clear()
