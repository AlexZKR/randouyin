import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from random import randint
from typing import Self

from fastapi import HTTPException, status
from playwright.async_api import BrowserContext, Page, TimeoutError

from randouyin.adapters.scraper.utils.antiblock import (
    random_waiting,
    simulate_human_behavior,
    simulate_scrolling,
)
from randouyin.adapters.scraper.utils.dead_end_handlers import (
    handle_log_in_to_view_content_de,
)
from randouyin.adapters.scraper.utils.popup_handlers import (
    handle_captcha_popup,
    handle_log_in_popup,
    handle_sign_in_popup,
)
from randouyin.adapters.scraper.utils.request_logger_decorator import RequestTimeLogger
from randouyin.adapters.scraper.utils.timeout_error_handler import (
    handle_timeout_crash,
)
from randouyin.config.settings import get_settings

logger = logging.getLogger("playwright")


class SearchPage:
    """Object with locators for `douyin.com/search/` page"""

    def __init__(self, context: BrowserContext, logger: RequestTimeLogger) -> None:
        self._input_loc = get_settings().scraping.SEARCH_PAGE_SEARCH_INTPUT_LOCATOR
        self._btn_loc = get_settings().scraping.SEARCH_PAGE_SEARCH_BTN_LOCATOR
        self._search_results_container_loc = (
            get_settings().scraping.SEARCH_LIST_CONTAINER_LOCATOR
        )

        self.context = context

        # Setup request logging
        self.__setup_request_logging(logger)
        self.requests_logger = logger

    async def open_search_page(self, query) -> Self:
        logger.info("Opening search page")
        try:
            # Setup page and wait for URL opening
            self.page = await self.context.new_page()
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            await self.page.goto(
                get_settings().scraping.DOUYIN_SEARCH_URL.format(query=query),
                wait_until="commit",
            )

            await simulate_scrolling(self.page)

            # Wait for btn and search input loading + random wait
            await self.page.wait_for_timeout(randint(1, 2000))
            await self.page.wait_for_selector(self._input_loc)
            await self.page.wait_for_selector(self._btn_loc)

            await simulate_human_behavior(self.page)

            # setup locators
            self._search_btn = self.page.locator(self._btn_loc)
            self._search_input = self.page.locator(self._input_loc)

            # Handle popups
            await handle_sign_in_popup(self.page)
            await handle_captcha_popup(self.page)
            await handle_log_in_popup(self.page)

            # handle dead ends
            await handle_log_in_to_view_content_de(self.page)

            logger.info("Opened search page")
            return self
        except TimeoutError as e:
            await handle_timeout_crash(
                page=self.page,
                e=e,
                requests_info=self.requests_logger.requests_log_msg,
                raise_exc=True,
            )

            # `handle_timeout_crash` here raises a HTTPException,
            # but type checker is not happy without `raise e`
            raise e

    @asynccontextmanager
    async def __search(self) -> AsyncGenerator:
        """Go back to search page after searching"""
        if not self.page:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Search page isn't loaded!",
            )
        await random_waiting()
        yield
        await simulate_human_behavior(self.page)
        logger.info("Returning to the search page")
        await self.page.go_back()

    async def perform_search(self, query: str) -> Page:
        logger.info(f"Searching for videos, query: {query}")
        async with self.__search():
            # html = await self.page.content()
            # if html:
            #     with open(f"randouyin/page.html", "w", encoding="utf-8") as f:
            #         f.write(html)
            # await self.page.screenshot(path="randouyin/page.png")

            # Input query and press the btn
            # await self._search_input.fill(query)
            # await self.page.wait_for_timeout(randint(1, 100))
            # await self._search_btn.click()

            # Wait for results to load
            await simulate_scrolling(self.page)

            logger.info("Waiting for initial results to load")
            await self.page.wait_for_selector(self._search_results_container_loc)
            return self.page

    def __setup_request_logging(self, logger: RequestTimeLogger) -> None:
        """Setup logging of requests made during scraping operations"""
        # decorator logging of open_search_page
        original = self.__class__.open_search_page
        decorated = logger(original).__get__(self, self.__class__)
        self.open_search_page = decorated  # type: ignore[method-assign]
