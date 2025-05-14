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
        while True:
            logger.info(f"Searching for videos, query: {query}")
            page = await self.browser.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(
                get_settings().scraping.DOUYIN_SEARCH_URL.format(query=query)
            )
            await page.wait_for_load_state(
                "domcontentloaded",
                timeout=get_settings().scraping.SEARCH_PAGE_LOADING_TIMEOUT,
            )
            items = page.locator(get_settings().scraping.SEARCH_LIST_CONTAINER_LOCATOR)
            html_video_cards: list[str] = await items.evaluate_all(
                "nodes => nodes.map(n => n.outerHTML)"
            )
            # TODO: swap page closing for scrolling
            await page.close()
            if len(html_video_cards) > 0:
                break
        return html_video_cards

    async def get_video(self, id: int) -> str:
        page = await self.browser.new_page()
        await page.goto(get_settings().scraping.DOUYIN_VIDEO_URL.format(id=id))
        item = page.locator(get_settings().scraping.SINGLE_VIDEO_TAG)
        video_tag: str = await item.evaluate("el => el.outerHTML")
        await page.close()
        return video_tag
