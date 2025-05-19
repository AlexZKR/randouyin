import json
import logging
import time
from collections import defaultdict
from os import path

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from randouyin.config.settings import get_settings
from randouyin.ports.base_scraper import BaseScraper

logger = logging.getLogger("playwright")

COOKIE_PATH = "randouyin/config/cookies.json"


class PlaywrightScraper(BaseScraper):
    async def __aenter__(self):
        logger.info("Setting up headless browser")
        self._playwright = await Stealth().use_async(async_playwright()).__aenter__()
        self.browser = await self._playwright.chromium.launch(
            headless=get_settings().scraping.USE_HEADLESS_BROWSER,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
            ],
        )
        self.cookies = None
        self.context = await self.browser.new_context()
        if path.exists(COOKIE_PATH):
            with open(COOKIE_PATH) as f:
                self.cookies = json.load(f)
            logger.info(f"Loaded cookies:\n{self.cookies}")
            await self.context.add_cookies(self.cookies)

        async def stub_security(route, request):
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
                # Respond instantly with an empty function stub
                await route.fulfill(
                    status=200,
                    content_type="application/javascript",
                    body="/* stubbed security SDK */\nwindow.__sdk_stub = true;",
                )
            else:
                await route.continue_()

        # Apply at context level so all pages share it
        await self.context.add_init_script("delete navigator.serviceWorker;")
        await self.context.route("**/*", stub_security)

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

        await self.browser.close()
        await self._playwright.stop()

    async def search_videos(self, query: str) -> list[str]:
        # Record overall start
        overall_start = time.monotonic()

        # Dicts to hold timing info
        request_starts: dict[str, float] = {}
        durations: dict[str, float] = defaultdict(float)

        while True:
            logger.info(f"Searching for videos, query: {query}")
            page = await self.context.new_page()

            # Listen for request start

            await page.set_viewport_size({"width": 3840, "height": 2160})
            await page.goto(
                get_settings().scraping.DOUYIN_SEARCH_URL.format(query=query),
                wait_until="commit",
            )
            # await page.wait_for_load_state(
            #     "load",
            #     timeout=get_settings().scraping.SEARCH_PAGE_LOADING_TIMEOUT,
            # )
            page.on(
                "request",
                lambda request: request_starts.setdefault(
                    request.url, time.monotonic()
                ),
            )
            # page.on(
            #     "request",
            #     lambda request: logger.info(f"<< {request.method}, {request.url}"),
            # )
            # page.on(
            #     "response",
            #     lambda response: logger.info(f"<< {response.status}, {response.url}"),
            # )
            # block specific requests first
            await page.route(
                "**/collect/5.1/collect.zip.js*", lambda route: route.abort()
            )
            await page.route("**/*.{png,jpg,jpeg}", lambda route: route.abort())
            await page.route("**/*ad*.js", lambda r: r.abort())
            # Abort based on the request type
            await page.route(
                "**/*",
                lambda route: route.abort()
                if route.request.resource_type
                in {
                    "image",  # pictures
                    "stylesheet",  # CSS
                    "font",  # custom fonts
                    "media",  # audio/video
                    "texttrack",  # subtitles/captions
                    "eventsource",  # server-sent events
                    "websocket",  # live socket traffic
                    "manifest",  # webapp manifests
                    "other",  # prefetch, beacon, etc.
                }
                else route.continue_(),
            )

            async def on_request_done(request_or_response):
                url = request_or_response.url
                start = request_starts.get(url)
                if start:
                    end = time.monotonic()
                    durations[url] = end - start

            page.on("requestfinished", on_request_done)
            page.on("requestfailed", on_request_done)

            await page.wait_for_selector(
                get_settings().scraping.SEARCH_LIST_CONTAINER_LOCATOR
            )
            items = page.locator(get_settings().scraping.SEARCH_LIST_CONTAINER_LOCATOR)
            html_video_cards: list[str] = await items.evaluate_all(
                "nodes => nodes.map(n => n.outerHTML)"
            )
            # TODO: swap page closing for scrolling
            await page.close()

            if len(html_video_cards) > 0:
                break

        overall_end = time.monotonic()
        total_seconds = overall_end - overall_start

        # Sort URLs by duration, descending
        sorted_requests = sorted(durations.items(), key=lambda kv: kv[1], reverse=True)

        # Log the slowest 10 requests
        logger.info(f"Total search_videos time: {total_seconds:.2f}s")
        logger.info("Top 10 slowest requests:")
        for url, dur in sorted_requests[:10]:
            logger.info(f"   {dur:.3f}s — {url}")
        return html_video_cards

    async def get_video(self, id: int) -> str:
        page = await self.browser.new_page()
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
