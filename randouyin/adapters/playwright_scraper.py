import http
import json
import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass
from os import path

from fastapi import HTTPException
from playwright.async_api import Locator, Page, async_playwright
from playwright_stealth import Stealth

from randouyin.config.settings import get_settings
from randouyin.ports.base_scraper import BaseScraper

logger = logging.getLogger("playwright")

COOKIE_PATH = "randouyin/config/cookies.json"
SEARCH_INPUT = 'input[data-e2e="searchbar-input"]'
SEARCH_BTN = 'button[data-e2e="searchbar-button"]'


class PlaywrightScraper(BaseScraper):
    # TODO: turn into decorator func!
    def __log_request_times(self, operation_name: str):
        overall_end = time.monotonic()
        total_seconds = overall_end - self.overall_start  # type: ignore

        # Sort URLs by duration, descending
        sorted_requests = sorted(
            self.durations.items(), key=lambda kv: kv[1], reverse=True
        )

        # Log the slowest 10 requests
        logger.info(f"Total operation {operation_name} time: {total_seconds:.2f}s")
        logger.info(f"Top 10 slowest requests for {operation_name}:")
        for url, dur in sorted_requests[:10]:
            logger.info(f"   {dur:.3f}s — {url}")

        # clear requests log for new requests
        self.durations.clear()
        self.request_starts.clear()

    async def __prepare_context(self) -> None:
        self.context = await self._browser.new_context()

        self.overall_start = time.monotonic()
        self.request_starts: dict[str, float] = {}
        self.durations: dict[str, float] = defaultdict(float)

        self.context.on(
            "request", lambda r: self.request_starts.setdefault(r.url, time.monotonic())
        )
        # self.context.on(
        #     "request", lambda r: setattr(self, "overall_start", time.monotonic())
        # )

        async def on_request_done(request_or_response):
            url = request_or_response.url
            start = self.request_starts.get(url)
            if start:
                end = time.monotonic()
                self.durations[url] = end - start

        self.context.on("requestfinished", on_request_done)
        self.context.on("requestfailed", on_request_done)

        # loading cookies
        if path.exists(COOKIE_PATH):
            with open(COOKIE_PATH) as f:
                self.cookies = json.load(f)
            logger.info(f"Loaded cookies:\n{self.cookies}")
            await self.context.add_cookies(self.cookies)

        # request interceptions
        async def __stub_security(route, request):
            url = request.url
            # Match all known security SDK patterns
            if any(
                domain in url
                for domain in [
                    "secsdk-lastest.umd.js",
                    "webmssdk.es5.js",
                    "sdk-glue.js",
                    "monitor_browser/collect",
                    "strategy_90.js",
                    "runtime.js",
                    "collect",
                    "security-secsdk",
                ]
            ):
                await route.fulfill(
                    status=200,
                    content_type="application/javascript",
                    body="/* stubbed security SDK */\nwindow.__sdk_stub = true;",
                )
            else:
                await route.continue_()

        await self.context.add_init_script("delete navigator.serviceWorker;")
        await self.context.route("**/*", __stub_security)

        await self.context.route(
            "**/collect/5.1/collect.zip.js*", lambda route: route.abort()
        )
        await self.context.route("**/*.{png,jpg,jpeg}", lambda route: route.abort())
        await self.context.route("**/*ad*.js", lambda r: r.abort())
        await self.context.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type
            in {
                "image",
                "stylesheet",
                "font",
                "media",
                "texttrack",
                "eventsource",
                "websocket",
                "manifest",
                "other",
            }
            else route.continue_(),
        )

        await self.context.route(
            "**/webmssdk.es5.js",
            lambda r: r.fulfill(
                status=200, content_type="application/javascript", body=""
            ),
        )
        await self.context.route(
            "**/sdk-glue.js",
            lambda r: r.fulfill(
                status=200, content_type="application/javascript", body=""
            ),
        )

    async def __aenter__(self):
        logger.info("Setting up headless browser")
        self._playwright = await Stealth().use_async(async_playwright()).__aenter__()
        self._browser = await self._playwright.chromium.launch(
            headless=get_settings().scraping.USE_HEADLESS_BROWSER,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
            ],
        )
        self.cookies = None

        await self.__prepare_context()
        await self.__open_search_page()

        return self

    async def __aexit__(self, exc_type, exc, tb):
        logger.info("Tearing down headless browser")

        # extracting cookies
        all_cookies = await self.context.cookies()
        if self.cookies != all_cookies:
            logger.info(f"Saving cookies:\n{all_cookies}")
            with open(COOKIE_PATH, "w") as f:
                f.write(json.dumps(all_cookies))
        else:
            logger.info("Cookies didn't change!")

        await self.context.close()
        await self._browser.close()
        await self._playwright.stop()

    @dataclass
    class SearchPage:
        search_btn: Locator
        search_input: Locator
        search_page: Page

    async def __open_search_page(self):
        """Open search page after initialization"""
        logger.info("Opening search page")
        search_page = await self.context.new_page()
        await search_page.set_viewport_size({"width": 3840, "height": 2160})
        await search_page.goto(
            get_settings().scraping.DOUYIN_SEARCH_URL,
            wait_until="commit",
        )

        await search_page.wait_for_selector(SEARCH_INPUT)
        await search_page.wait_for_selector(SEARCH_BTN)

        self.search_page = self.SearchPage(
            search_input=search_page.locator(SEARCH_INPUT),
            search_btn=search_page.locator(SEARCH_BTN),
            search_page=search_page,
        )
        self.__log_request_times(operation_name="open_search_page")
        logger.info("Opened search page")

    @asynccontextmanager
    async def __search(self):
        """Sitting idle on the search page, until a request comes.
        After search request fullfilled, return back to the search page.

        TODO: handle open in app popups

        """
        if not self.search_page:
            raise HTTPException(
                status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Search page isn't loaded!",
            )

        yield self.search_page

        logger.info("Returning to the search page")
        await self.search_page.search_page.go_back()

    async def search_videos(self, query: str) -> list[str]:
        SCROLLING_TIMES = 5
        i = 0
        results = []
        async with self.__search() as sp:
            self.overall_start = time.monotonic()
            while True:
                logger.info(f"Searching for videos, query: {query}")
                await sp.search_input.fill(query)
                await sp.search_btn.click()
                await sp.search_page.wait_for_selector(
                    get_settings().scraping.SEARCH_LIST_CONTAINER_LOCATOR
                )
                items = sp.search_page.locator(
                    get_settings().scraping.SEARCH_LIST_CONTAINER_LOCATOR
                )
                html_video_cards: list[str] = await items.evaluate_all(
                    "nodes => nodes.map(n => n.outerHTML)"
                )
                results.extend(html_video_cards)
                logger.info(f"Got {len(html_video_cards)} for iteration {i}")
                if len(html_video_cards) > 0:
                    await sp.search_page.mouse.wheel(0, 300)
                    i += 1
                    if i == SCROLLING_TIMES:
                        logger.info(f"Break after iteration {i}")
                        break
        logger.info(f"Returning {len(results)} videos total")
        self.__log_request_times(operation_name="search_videos_by_query")
        return results

    async def get_video(self, id: int) -> str:
        page = await self._browser.new_page()
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
