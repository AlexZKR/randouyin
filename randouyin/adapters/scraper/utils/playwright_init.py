import logging

from playwright.async_api import BrowserContext, async_playwright
from playwright_stealth import Stealth

from randouyin.adapters.scraper.utils.cookie_manager import PWCookieManager
from randouyin.adapters.scraper.utils.request_interception import (
    set_request_interceptions,
)
from randouyin.config.settings import get_settings

logger = logging.getLogger("playwright")

BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-gpu",
]


class PWManager:
    """Manages PW and browser instances"""

    def __init__(self) -> None:
        self.cookie_manager = PWCookieManager()

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

        return self.context

    # async def __prepare_context(self) -> None:
    #     # request time measuring
    #     self.overall_start = time.monotonic()
    #     self.request_starts: dict[str, float] = {}
    #     self.durations: dict[str, float] = defaultdict(float)

    #     self.context.on(
    #         "request", lambda r: self.request_starts.setdefault(r.url, time.monotonic())
    #     )

    #     async def on_request_done(request_or_response):
    #         url = request_or_response.url
    #         start = self.request_starts.get(url)
    #         if start:
    #             end = time.monotonic()
    #             self.durations[url] = end - start

    #     self.context.on("requestfinished", on_request_done)
    #     self.context.on("requestfailed", on_request_done)
