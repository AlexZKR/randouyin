import logging

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from randouyin.config.settings import get_settings
from randouyin.ports.base_scraper import BaseScraper

logger = logging.getLogger("playwright")


class PlaywrightScraper(BaseScraper):
    async def __aenter__(self):
        logger.info("Setting up headless browser")
        self._playwright = await Stealth().use_async(async_playwright()).__aenter__()
        self.browser = await self._playwright.chromium.launch(
            headless=get_settings().scraping.USE_HEADLESS_BROWSER
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        logger.info("Tearing down headless browser")
        await self.browser.close()
        await self._playwright.stop()

    async def search_videos(self, query: str) -> list[str]:
        """Outputs a list of video cards HTML

        Args:
            query (str): Query to search Douyin

        Returns:
            list[str]: list of video IDs
        """
        page = await self.browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.goto(get_settings().scraping.DOUYIN_SEARCH_URL.format(query=query))
        items = page.locator(get_settings().scraping.SEARCH_LIST_CONTAINER_LOCATOR)
        html_video_cards: list[str] = await items.evaluate_all(
            "nodes => nodes.map(n => n.outerHTML)"
        )
        return html_video_cards
