import functools
import logging
import time
from collections import defaultdict
from collections.abc import Callable

from playwright.async_api import BrowserContext, Request

from randouyin.config.settings import get_settings

logger = logging.getLogger("playwright")


class RequestTimeLogger:
    """Class-based decorator that tracks durations of context's requests"""

    def __init__(self, context: BrowserContext) -> None:
        self.request_start_times: dict[str, float] = {}

        self.success_request_durations: dict[str, float] = defaultdict(float)
        self.failed_request_durations: dict[str, float] = defaultdict(float)

        self.total_seconds: float
        self.operation_name: str
        self.requests_log_msg: str = ""

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

            self.success_request_durations.clear()
            self.failed_request_durations.clear()
            self.request_start_times.clear()
            return result

        return wrapper

    def log_durations(self) -> None:
        """Sorts request durations and outputs to logger"""
        duration_threshold = get_settings().scraping.SLOWNESS_THRESHOLD_MS

        def format_top_requests(requests, threshold, max_items=10):
            lines = [
                f"   {duration:.2f}s — {url}"
                for url, duration in requests[:max_items]
                if duration > threshold
            ]
            return "\n".join(lines) if lines else None

        sorted_success = sorted(
            self.success_request_durations.items(), key=lambda kv: kv[1], reverse=True
        )
        sorted_failed = sorted(
            self.failed_request_durations.items(), key=lambda kv: kv[1], reverse=True
        )

        total_time = (
            f"Total operation {self.operation_name} time: {self.total_seconds:.2f}s"
        )
        slowest_heading = "Top 10 slowest requests (note: requests are made in parallel, so durations can't be summed up to get total duration): "

        slow_success = format_top_requests(sorted_success, duration_threshold)
        slow_failed = format_top_requests(sorted_failed, duration_threshold)

        if not slow_success:
            slow_success = f"No requests, slower than {duration_threshold / 1000} sec."
        else:
            slow_success = "\n" + slow_success

        if not slow_failed:
            slow_failed = "No failed requests!"
        else:
            slow_failed = "\n" + slow_failed

        failed_heading = "Failed requests: "

        # Compose log message
        self.requests_log_msg = (
            f"{total_time}\n\n"
            f"{slowest_heading}{slow_success}\n\n"
            f"{failed_heading}\n{slow_failed}\n"
        )
        logger.info(self.requests_log_msg)

    def on_request_start(self, r: Request) -> None:
        """Callback that's called when request fires, to record it's start time"""
        self.request_start_times[r.url] = time.monotonic()

    def on_request_finish(self, r: Request):
        """Callback that's called after request has been done, to record it's end time"""
        url = r.url
        start = self.request_start_times.get(url)
        end = time.monotonic()
        if start:
            if r.failure:
                self.failed_request_durations[f"{r.failure} - {url}"] = end - start
            else:
                self.success_request_durations[url] = end - start
