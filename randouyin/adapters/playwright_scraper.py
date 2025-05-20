import http
import json
import logging
import random
import time
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from os import path

import playwright
import playwright.async_api
from fastapi import HTTPException
from playwright.async_api import Locator, Page, async_playwright
from playwright_stealth import Stealth

from randouyin.adapters.beautiful_soup_parser import BeautifulSoupParser
from randouyin.config.settings import get_settings
from randouyin.ports.base_scraper import BaseScraper

logger = logging.getLogger("playwright")


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

        async def on_request_done(request_or_response):
            url = request_or_response.url
            start = self.request_starts.get(url)
            if start:
                end = time.monotonic()
                self.durations[url] = end - start

        self.context.on("requestfinished", on_request_done)
        self.context.on("requestfailed", on_request_done)

        # loading cookies
        if path.exists(get_settings().scraping.COOKIE_PATH):
            with open(get_settings().scraping.COOKIE_PATH) as f:
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
        # Block any font file by extension
        await self.context.route("**/*.woff2", lambda r: r.abort())
        await self.context.route("**/*.ttf", lambda r: r.abort())

        # Block CSS via glob
        await self.context.route("**/*.css", lambda r: r.abort())
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
        try:
            logger.info("Opening search page")
            search_page = await self.context.new_page()
            await search_page.set_viewport_size({"width": 3840, "height": 2160})
            await search_page.goto(
                get_settings().scraping.DOUYIN_SEARCH_URL,
                wait_until="commit",
            )

            # random waiting
            # await search_page.wait_for_timeout(random.randint(1, 2000))

            await search_page.wait_for_selector(SEARCH_INPUT)
            await search_page.wait_for_selector(SEARCH_BTN)

            self.search_page = self.SearchPage(
                search_input=search_page.locator(SEARCH_INPUT),
                search_btn=search_page.locator(SEARCH_BTN),
                search_page=search_page,
            )
            self.__log_request_times(operation_name="open_search_page")
            logger.info("Opened search page")
        except Exception as e:
            await self.handle_crash(e, self.search_page.search_page)

        # extracting cookies
        all_cookies = await self.context.cookies()
        if self.cookies != all_cookies and path.exists(
            path.dirname(get_settings().scraping.COOKIE_PATH)
        ):
            logger.info(f"Saving cookies:\n{all_cookies}")
            with open(get_settings().scraping.COOKIE_PATH, "w") as f:
                f.write(json.dumps(all_cookies))
        else:
            logger.info("Cookies didn't change!")

    @asynccontextmanager
    async def __search(self) -> AsyncGenerator[SearchPage]:
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

    async def search_videos(self, query: str) -> list[str]:  # noqa: PLR0915
        SCROLLING_TIMES = 3
        EMPTY_RESULTS_THRESHOLD = 5
        i = 0
        empty_results_counter = 0
        results = []
        ids = set()
        async with self.__search() as sp:
            try:
                self.overall_start = time.monotonic()
                logger.info(f"Searching for videos, query: {query}")

                await sp.search_input.fill(query)
                await sp.search_btn.click()
                await sp.search_page.wait_for_selector(
                    get_settings().scraping.SEARCH_LIST_CONTAINER_LOCATOR
                )
                while True:
                    await sp.search_page.wait_for_timeout(random.randint(1, 1000))
                    items = sp.search_page.locator(
                        get_settings().scraping.SEARCH_LIST_CONTAINER_LOCATOR
                    )

                    # CAPTCHA CHECK
                    logger.info("Checking for CAPTCHA...")
                    if await self.is_captcha_present(sp.search_page):
                        # 1) take screenshot
                        await sp.search_page.screenshot(
                            path="randouyin/captcha.png", full_page=True
                        )
                        # 2) handle: raise, redirect, or bail out
                        raise Exception(
                            "CAPTCHA detected – screenshot saved to captcha.png"
                        )
                    logger.info("No CAPTCHA")
                    await sp.search_page.mouse.move(
                        random.randint(1, 800), random.randint(1, 600)
                    )

                    # POPUP HANDLING

                    # 1. sign in to continue
                    # please sign in pop up text - 请登录后继续使用
                    # cancel - 取消
                    # sure - 确定

                    popup_locator = sp.search_page.get_by_text(
                        "请登录后继续使用", exact=False
                    )

                    async def dismiss_login_popup():
                        # Log for visibility
                        logger.info("Detected sign-in popup—clicking '取消'")
                        cancel_locator = sp.search_page.get_by_text("取消", exact=False)
                        await cancel_locator.click()

                    # Register the handler; opt out of waiting for the overlay to vanish
                    await sp.search_page.add_locator_handler(
                        popup_locator, handler=dismiss_login_popup, no_wait_after=True
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
                    await sp.search_page.wait_for_timeout(random.randint(1, 2000))

                    results.extend(html_video_cards)
                    logger.info(
                        f"Got {len(html_video_cards)} for iteration {i}, total: {len(ids)}"
                    )
                    if len(html_video_cards) > 0:
                        # await items.last.scroll_into_view_if_needed()
                        await sp.search_page.keyboard.press("End")
                        i += 1
                        if i == SCROLLING_TIMES:
                            logger.info(f"Break after iteration {i}")
                            break
                    elif empty_results_counter > EMPTY_RESULTS_THRESHOLD:
                        logger.info(
                            "Empty results threshold exceeded! Returning results"
                        )
                        break
                    else:
                        empty_results_counter += 1

                logger.info(f"Returning {len(results)} videos total")
                self.__log_request_times(operation_name="search_videos_by_query")
                return list(results)
            except playwright.async_api.TimeoutError as e:
                await self.handle_crash(e, sp.search_page)
                # if timeout happend and some videos were scraped - return them
                if len(results) > 0:
                    return list(results)
                else:
                    return []
            except Exception as e:
                # take screenshot of crash and save HTML
                await self.handle_crash(e, sp.search_page)
                raise e

    async def handle_crash(self, e: Exception, page: Page):
        # Playwright’s error message tells us a blocking element’s selector

        await page.screenshot(path="randouyin/crash.png")
        html = await page.text_content("body")
        # Save HTML to file
        with open("randouyin/crash.html", "w", encoding="utf-8") as f:
            f.write(html)
        # Re-raise so your crash logic still triggers
        raise e

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
