import logging

import pytest
from randouyin.ports.base_scraper import BaseScraper

logger = logging.getLogger("test")


@pytest.mark.asyncio
class TestDouyinScraping:
    @pytest.mark.parametrize("query, expectation", [("童笑", "")])
    async def test_video_search(
        self, scraper: BaseScraper, query: str, expectation: str
    ) -> None:
        """Video search returns list of video ids"""
        async with scraper as s:
            result = await s.search_videos(query=query)
            assert result == expectation, (
                f"Received video ids didn't match the expectation\n{expectation}"
            )
