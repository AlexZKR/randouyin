import logging
from collections.abc import Generator
from typing import Any

import pytest
import pytest_asyncio
from randouyin.adapters.httpx_client import HttpxClient
from randouyin.config.settings import get_settings
from randouyin.ports.base_client import BaseClient

logger = logging.getLogger("test")


@pytest_asyncio.fixture
async def client() -> BaseClient:
    logger.info("Setting up httpx test client")
    return HttpxClient()


@pytest.fixture
def get_clean_settings_between_tests() -> Generator[None, Any, Any]:
    yield
    get_settings.cache_clear()
