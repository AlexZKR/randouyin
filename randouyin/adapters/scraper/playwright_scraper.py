import logging
import random

import playwright
import playwright.async_api
from playwright.async_api import Page

from randouyin.adapters.beautiful_soup_parser import BeautifulSoupParser
from randouyin.adapters.scraper.models.search_page import SearchPage
from randouyin.adapters.scraper.utils.playwright_init import PWManager
from randouyin.config.settings import get_settings
from randouyin.ports.base_scraper import BaseScraper

logger = logging.getLogger("playwright")


class PlaywrightScraper(BaseScraper):
    # # TODO: turn into decorator func!
    # def __log_request_times(self, operation_name: str):
    #     overall_end = time.monotonic()
    #     total_seconds = overall_end - self.overall_start  # type: ignore

    #     # Sort URLs by duration, descending
    #     sorted_requests = sorted(
    #         self.durations.items(), key=lambda kv: kv[1], reverse=True
    #     )

    #     # Log the slowest 10 requests
    #     logger.info(f"Total operation {operation_name} time: {total_seconds:.2f}s")
    #     logger.info(f"Top 10 slowest requests for {operation_name}:")
    #     for url, dur in sorted_requests[:10]:
    #         logger.info(f"   {dur:.3f}s — {url}")

    #     # clear requests log for new requests
    #     self.durations.clear()
    #     self.request_starts.clear()

    async def __aenter__(self):
        self._pw_manager = PWManager()
        await self._pw_manager.start_pw()

        self.context = await self._pw_manager.get_context()

        self.search_page = await SearchPage().open_search_page(self.context)
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

        search_page = await self.search_page.perform_search(query)
        try:
            # self.overall_start = time.monotonic()
            while True:
                await search_page.wait_for_timeout(random.randint(1, 1000))
                items = search_page.locator(
                    get_settings().scraping.SEARCH_LIST_CONTAINER_LOCATOR
                )

                # # CAPTCHA CHECK
                # logger.info("Checking for CAPTCHA...")
                # if await self.is_captcha_present(sp.search_page):
                #     # 1) take screenshot
                #     await sp.search_page.screenshot(
                #         path="randouyin/captcha.png", full_page=True
                #     )
                #     # 2) handle: raise, redirect, or bail out
                #     raise Exception(
                #         "CAPTCHA detected – screenshot saved to captcha.png"
                #     )
                # logger.info("No CAPTCHA")
                await search_page.mouse.move(
                    random.randint(1, 800), random.randint(1, 600)
                )

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
                await search_page.wait_for_timeout(random.randint(1, 2000))

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
                # self.__log_request_times(operation_name="search_videos_by_query")
            return list(results)
        except playwright.async_api.TimeoutError:
            await self.handle_crash(search_page)
            # if timeout happend and some videos were scraped - return them
            if len(results) > 0:
                return list(results)
            else:
                return []
        except Exception as e:
            # take screenshot of crash and save HTML
            await self.handle_crash(search_page)
            raise e

    # TODO: MAKE as a decorator
    async def handle_crash(self, page: Page):
        await page.screenshot(path="randouyin/crash.png")

        html = await page.text_content("body")
        with open("randouyin/crash.html", "w", encoding="utf-8") as f:
            f.write(html)

    async def is_captcha_present(self, page: Page) -> bool:
        """
        Detect whether a CAPTCHA is blocking interaction.
        Returns True if a CAPTCHA container or iframe is found.
        """
        isCaptcha = False
        # 1) Look for a known overlay or container by ID or class
        if await page.query_selector("#captcha_container, .captcha-overlay"):
            isCaptcha = True

        # 2) Look for reCAPTCHA v2/v3 frames by URL pattern
        for frame in page.frames:
            url = frame.url
            if "google.com/recaptcha" in url or "hcaptcha.com" in url:
                isCaptcha = True

        # 3) (Optional) Detect common text prompts
        content = await page.content()
        if "Please verify you are a human" in content:
            isCaptcha = True

        if isCaptcha:
            if sel := await page.wait_for_selector(
                "div#captcha_container", timeout=20000
            ):
                with open("randouyin/captcha.html", "w") as f:
                    f.write(await sel.text_content())
            return True
        return False

    async def get_video(self, id: int) -> str:
        page = await self.context.new_page()
        await page.goto(
            get_settings().scraping.DOUYIN_VIDEO_URL.format(id=id), wait_until="commit"
        )
        await page.wait_for_selector(
            get_settings().scraping.SINGLE_VIDEO_TAG, state="attached"
        )
        item = page.locator(get_settings().scraping.SINGLE_VIDEO_TAG).first
        # await item.wait_for(state="attached", timeout=15000)

        video_tag: str = await item.evaluate("el => el.outerHTML")
        logger.info(video_tag)
        await page.close()
        return video_tag
