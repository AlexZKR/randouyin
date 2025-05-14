import json
import logging
from collections.abc import Generator
from typing import Any

import pytest
import pytest_asyncio
from randouyin.adapters.beautiful_soup_parser import BeautifulSoupParser
from randouyin.adapters.httpx_downloader import HttpxDownloader
from randouyin.adapters.playwright_scraper import PlaywrightScraper
from randouyin.config.settings import get_settings
from randouyin.ports.base_client import BaseClient
from randouyin.ports.base_parser import BaseParser
from randouyin.ports.base_scraper import BaseScraper

logger = logging.getLogger("test")


@pytest_asyncio.fixture
async def scraper() -> BaseScraper:
    logger.info("Setting up scraper test client")
    return PlaywrightScraper()


@pytest.fixture
def parser() -> BaseParser:
    logger.info("Setting up test parser")
    return BeautifulSoupParser()


@pytest_asyncio.fixture
async def downloader() -> BaseClient:
    logger.info("Setting up test downloader")
    return HttpxDownloader()


@pytest.fixture
def search_video_card_html() -> tuple[str, dict]:
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
def video_tag_html() -> tuple[str, dict, dict]:
    """Get one video HTML tag and related examples for parsing tests

    Returns:
        tuple[str, dict, dict]:
        str: example HTML;
        dict: dict of `ParsedVideo` model;
        dict: expected result (`SourcedVideo` model).
    """
    with open("tests/example/video_page/input.html") as f:
        html = f.read()

    from tests.example.video_page.example_video_model import (
        EXAMPLE_PARSED_VIDEO as example_model,
    )

    with open("tests/example/video_page/result.json") as f:
        result = json.load(f)
    return html, example_model, result


@pytest.fixture
def get_clean_settings_between_tests() -> Generator[None, Any, Any]:
    yield
    get_settings.cache_clear()
