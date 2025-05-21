import logging

from playwright.async_api import BrowserContext, async_playwright
from playwright_stealth import Stealth

from randouyin.adapters.scraper.utils.cookie_manager import PWCookieManager
from randouyin.adapters.scraper.utils.request_interception import (
    set_request_interceptions,
)
from randouyin.adapters.scraper.utils.request_logger_decorator import RequestTimeLogger
from randouyin.config.settings import get_settings

logger = logging.getLogger("playwright")

BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-gpu",
]


class PWManager:
    """Manages PW and browser context instances"""

    def __init__(self) -> None:
        self.cookie_manager = PWCookieManager()
        self.request_logger: RequestTimeLogger

    async def start_pw(self) -> None:
        headless = get_settings().scraping.USE_HEADLESS_BROWSER
        logger.info(
            f"Starting Playwright. Setting up browser: {'HEADLESS' if headless else 'HEADED'} mode"
        )

        self.__playwright = await Stealth().use_async(async_playwright()).__aenter__()
        self.__browser = await self.__playwright.chromium.launch(
            args=BROWSER_ARGS, headless=get_settings().scraping.USE_HEADLESS_BROWSER
        )

    async def close_pw(self):
        logger.info("Closing Playwright")
        await self.context.close()
        await self.__browser.close()
        await self.__playwright.stop()

    async def get_context(self) -> BrowserContext:
        self.context = await self.__browser.new_context()

        await self.cookie_manager.load_from_file(self.context)
        await set_request_interceptions(self.context)

        self.request_logger = RequestTimeLogger(self.context)

        return self.context
