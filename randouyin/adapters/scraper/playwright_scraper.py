import logging
from typing import Self

from playwright.async_api import TimeoutError

from randouyin.adapters.beautiful_soup_parser import BeautifulSoupParser
from randouyin.adapters.scraper.models.search_page import SearchPage
from randouyin.adapters.scraper.utils.antiblock import (
    random_waiting,
    simulate_human_behavior,
    simulate_scrolling,
)
from randouyin.adapters.scraper.utils.playwright_init import PWManager
from randouyin.adapters.scraper.utils.timeout_error_handler import (
    handle_timeout_crash,
)
from randouyin.config.settings import get_settings
from randouyin.ports.base_scraper import BaseScraper

logger = logging.getLogger("playwright")


class PlaywrightScraper(BaseScraper):
    async def __aenter__(self) -> Self:
        self._pw_manager = PWManager()

        await self._pw_manager.start_pw()
        self.context = await self._pw_manager.get_context()

        self.__setup_request_logging()

        self.sp = SearchPage(self.context, self._pw_manager.request_logger)

        await self._pw_manager.cookie_manager.save_to_file(self.context)

        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._pw_manager.close_pw()

    async def search_videos(self, query: str) -> list[str]:  # noqa: PLR0915
        SCROLLING_TIMES = 3
        EMPTY_RESULTS_THRESHOLD = 5
        i = 0
        empty_results_counter = 0
        results = []
        ids = set()

        try:
            # initial search
            self.search_page = await self.sp.open_search_page(query)

            search_page = await self.search_page.perform_search(query)

            # infinite scrolling
            while True:
                await random_waiting()
                items = search_page.locator(
                    get_settings().scraping.SEARCH_LIST_CONTAINER_LOCATOR
                )

                await simulate_human_behavior(search_page)

                html_video_cards: list[str] = [
                    card
                    for card in await items.evaluate_all(
                        "nodes => nodes.map(n => n.outerHTML)"
                    )
                    if BeautifulSoupParser().parse_id(card) not in ids
                ]
                for card in html_video_cards:
                    ids.add(BeautifulSoupParser().parse_id(card))

                    # random waiting
                await simulate_scrolling(search_page)

                results.extend(html_video_cards)
                logger.info(
                    f"Got {len(html_video_cards)} for iteration {i}, total: {len(ids)}"
                )
                if len(html_video_cards) > 0:
                    # await items.last.scroll_into_view_if_needed()
                    await search_page.keyboard.press("End")
                    i += 1
                    if i == SCROLLING_TIMES:
                        logger.info(f"Break after iteration {i}")
                        break
                elif empty_results_counter > EMPTY_RESULTS_THRESHOLD:
                    logger.info("Empty results threshold exceeded! Returning results")
                    break
                else:
                    empty_results_counter += 1

                logger.info(f"Returning {len(results)} videos total")
                if len(results) == 0:
                    raise TimeoutError("Results is 0")
            return list(results)
        except TimeoutError as e:
            # if timeout happend and some videos were scraped - return them
            timeout_id = await handle_timeout_crash(
                page=self.search_page.page,
                e=e,
                requests_info=self._pw_manager.request_logger.requests_log_msg,
                raise_exc=False,
            )
            logger.error(
                f"A timeout happened during video search. Search resulted in {len(results)} videos.\ntimeout_id: {timeout_id}"
            )
            if len(results) > 0:
                return list(results)
            return []

    async def get_video(self, id: int) -> str:
        page = await self.context.new_page()
        await page.goto(
            get_settings().scraping.DOUYIN_VIDEO_URL.format(id=id), wait_until="commit"
        )
        await page.wait_for_selector(
            get_settings().scraping.SINGLE_VIDEO_TAG_LOCATOR, state="attached"
        )
        item = page.locator(get_settings().scraping.SINGLE_VIDEO_TAG_LOCATOR).first

        video_tag: str = await item.evaluate("el => el.outerHTML")
        logger.info(video_tag)
        await page.close()
        return video_tag

    def __setup_request_logging(self) -> None:
        """Setup logging of requests made during scraping operations"""
        logger = self._pw_manager.request_logger

        # decorator logging of search_videos
        original = self.__class__.search_videos  # type: ignore[assignment]
        decorated = logger(original).__get__(self, self.__class__)
        self.search_videos = decorated  # type: ignore[method-assign]

        # decorator logging of get_video
        original = self.__class__.get_video  # type: ignore[assignment]
        decorated = logger(original).__get__(self, self.__class__)
        self.get_video = decorated  # type: ignore[method-assign]
