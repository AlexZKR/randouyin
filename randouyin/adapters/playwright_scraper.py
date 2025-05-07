import logging

from playwright.async_api import async_playwright

from randouyin.config.settings import get_settings
from randouyin.ports.base_scraper import BaseScraper

logger = logging.getLogger("playwright")


class PlaywrightScraper(BaseScraper):
    async def __aenter__(self):
        logger.info("Setting up headless browser")
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=True)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        logger.info("Tearing down headless browser")
        await self.browser.close()
        await self._playwright.stop()

    async def search_videos(self, query: str) -> list[str]:
        page = await self.browser.new_page()
        await page.goto(get_settings().scraping.douyin_search_url.format(query=query))
        divs = page.locator("div[id^='waterfall_item']")
        ids = await divs.evaluate_all("divs => divs.map(div => div.id)")
        return [id for id in ids]
