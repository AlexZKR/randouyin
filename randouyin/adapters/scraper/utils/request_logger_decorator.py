import functools
import logging
import time
from collections import defaultdict
from collections.abc import Callable

from playwright.async_api import BrowserContext, Request

logger = logging.getLogger("playwright")


class RequestTimeLogger:
    """Class-based decorator that tracks durations of context's requests"""

    def __init__(self, context: BrowserContext) -> None:
        self.request_start_times: dict[str, float] = {}

        self.success_request_durations: dict[str, float] = defaultdict(float)
        self.failed_request_durations: dict[str, float] = defaultdict(float)

        self.total_seconds: float
        self.operation_name: str
        self.requests_log_msg: str

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
        sorted_success_requests = sorted(
            self.success_request_durations.items(), key=lambda kv: kv[1], reverse=True
        )
        sorted_failed_requests = sorted(
            self.failed_request_durations.items(), key=lambda kv: kv[1], reverse=True
        )
        total_time_str = (
            f"Total operation {self.operation_name} time: {self.total_seconds:.2f}s"
        )
        ten_slowest_successful_heading = "Top 10 slowest requests (note: requests are made in parallel, so durations can't be sumed up to get total duration):"

        success_slowest_durations_str = ""
        for url, dur in sorted_success_requests[:10]:
            success_slowest_durations_str += f"   {dur:.3f}s — {url}\n"

        failed_requests_heading = "Failed requests:"
        failed_durations = ""
        for url, dur in sorted_failed_requests[:10]:
            failed_durations += f"   {dur:.3f}s — {url}\n"

        # saving for error stack
        self.requests_log_msg = (
            total_time_str
            + "\n\n"
            + ten_slowest_successful_heading
            + "\n"
            + success_slowest_durations_str
            + "\n"
            + failed_requests_heading
            + "\n"
            + failed_durations
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
