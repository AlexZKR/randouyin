import logging

import pytest
from randouyin.ports.base_scraper import BaseScraper

from tests.scraping_assumptions import NUM_VIDEOS_ON_SEARCH

logger = logging.getLogger("test")


@pytest.mark.asyncio
class TestDouyinScraping:
    @pytest.mark.parametrize(
        "query, result_expectation", [("童笑", NUM_VIDEOS_ON_SEARCH)]
    )
    async def test_video_search(
        self, scraper: BaseScraper, query: str, result_expectation: int
    ) -> None:
        """Video search returns list of video cards HTMLs"""
        async with scraper as s:
            result = await s.search_videos(query=query)
            assert len(result) == result_expectation, (
                f"Number of found videos didn't match the expectation. Found: {len(result)}, expected: {NUM_VIDEOS_ON_SEARCH}\n\n{result}"
            )
