import logging

import pytest
from randouyin.ports.base_scraper import BaseScraper

logger = logging.getLogger("test")


@pytest.mark.asyncio
class TestDouyinScraping:
    @pytest.mark.parametrize("query", [("童笑")])
    async def test_video_search(self, scraper: BaseScraper, query: str) -> None:
        """Video search returns list of video cards HTMLs"""
        async with scraper as s:
            result = await s.search_videos(query=query)
            assert len(result) > 0, "Number of found videos is 0"

    @pytest.mark.parametrize("id", [(7501650862555008308)])
    async def test_single_video_scraping(self, scraper: BaseScraper, id: int) -> None:
        """Single video scraping returns HTML <video> tag"""
        async with scraper as s:
            result = await s.get_video(id=id)
            assert "src" in result, "no `src` tag in parsed result"
