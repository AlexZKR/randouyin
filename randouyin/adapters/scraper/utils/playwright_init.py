import logging
from random import choice

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
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-blink-features",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.2420.81",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux i686; rv:124.0) Gecko/20100101 Firefox/124.0",
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
        self.context = await self.__browser.new_context(user_agent=choice(USER_AGENTS))

        await self.cookie_manager.load_from_file(self.context)
        await set_request_interceptions(self.context)

        self.request_logger = RequestTimeLogger(self.context)

        return self.context
