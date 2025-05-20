import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from random import randint
from typing import Self

from fastapi import HTTPException, status
from playwright.async_api import BrowserContext, Page
from randouyin.adapters.scraper.utils.sign_in_popup import handle_sign_in_popup
from randouyin.config.settings import get_settings

logger = logging.getLogger("playwright")


class SearchPage:
    """Object with locators for `douyin.com/search/` page"""

    def __init__(self) -> None:
        self._input_loc = get_settings().scraping.SEARCH_PAGE_SEARCH_INTPUT_LOCATOR
        self._btn_loc = get_settings().scraping.SEARCH_PAGE_SEARCH_BTN_LOCATOR
        self._search_results_container_loc = (
            get_settings().scraping.SEARCH_LIST_CONTAINER_LOCATOR
        )

    # TODO: log request times
    # self.__log_request_times(operation_name="open_search_page")
    async def open_search_page(self, context: BrowserContext) -> Self:
        logger.info("Opening search page")

        # Setup page and wait for URL opening
        self.search_page = await context.new_page()
        await self.search_page.set_viewport_size({"width": 3840, "height": 2160})
        await self.search_page.goto(
            get_settings().scraping.DOUYIN_SEARCH_URL,
            wait_until="commit",
        )

        # Wait for btn and search input loading + random wait
        await self.search_page.wait_for_timeout(randint(1, 2000))
        await self.search_page.wait_for_selector(self._input_loc)
        await self.search_page.wait_for_selector(self._btn_loc)

        # setup locators
        self._search_btn = self.search_page.locator(self._btn_loc)
        self._search_input = self.search_page.locator(self._input_loc)

        # Handle popups
        await handle_sign_in_popup(self.search_page)

        logger.info("Opened search page")
        return self

    @asynccontextmanager
    async def __search(self) -> AsyncGenerator:
        """Go back to search page after searching"""
        if not self.search_page:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Search page isn't loaded!",
            )

        yield

        logger.info("Returning to the search page")
        await self.search_page.go_back()

    async def perform_search(self, query: str) -> Page:
        logger.info(f"Searching for videos, query: {query}")
        async with self.__search():
            # Input query and press the btn
            await self._search_input.fill(query)
            await self._search_btn.click()

            # Wait for results to load
            await self.search_page.wait_for_selector(self._search_results_container_loc)
            return self.search_page
