import functools
import logging
import time
from collections import defaultdict
from collections.abc import Callable

from playwright.async_api import BrowserContext, Request, Response

logger = logging.getLogger("playwright")


class RequestTimeLogger:
    """Class-based decorator that tracks durations of context's requests"""

    def __init__(self, context: BrowserContext) -> None:
        self.request_start_times: dict[str, float] = {}
        self.request_durations: dict[str, float] = defaultdict(float)

        self.total_seconds: float
        self.operation_name: str

        # Register callbacks
        logger.info("Setting up logger - registering callbacks on context")
        context.on("request", self.on_request_start)
        context.on("requestfinished", self.on_request_finish)
        context.on("requestfailed", self.on_request_finish)

        self.context = context

    def __call__(
        self,
        func: Callable,
    ) -> Callable:
        functools.wraps(func)

        async def wrapper(*args, **kwargs):
            start_time = time.monotonic()
            result = await func(*args, **kwargs)
            end_time = time.monotonic()

            self.total_seconds = end_time - start_time
            self.operation_name = func.__name__
            self.log_durations()

            self.request_durations.clear()
            self.request_start_times.clear()
            return result

        return wrapper

    def log_durations(self) -> None:
        """Sorts request durations and outputs to logger"""
        sorted_requests = sorted(
            self.request_durations.items(), key=lambda kv: kv[1], reverse=True
        )
        logger.info(
            f"Total operation {self.operation_name} time: {self.total_seconds:.2f}s"
        )
        logger.info(
            "Top 10 slowest requests (note: requests are made in parallel, so durations can't be sumed up to get total duration):"
        )
        for url, dur in sorted_requests[:10]:
            logger.info(f"   {dur:.3f}s — {url}")

    def on_request_start(self, r: Request) -> None:
        """Callback that's called when request fires, to record it's start time"""
        self.request_start_times[r.url] = time.monotonic()

    def on_request_finish(self, r: Request | Response):
        """Callback that's called after request has been done, to record it's end time"""
        url = r.url
        start = self.request_start_times.get(url)
        if start:
            end = time.monotonic()
            self.request_durations[url] = end - start
