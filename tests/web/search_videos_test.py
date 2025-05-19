import logging

import pytest
from fastapi import status
from httpx import AsyncClient

logger = logging.getLogger("test")


class TestDouyinScraping:
    @pytest.mark.parametrize("query", [("fireworks")])
    async def test_video_search(self, async_client: AsyncClient, query: str) -> None:
        """Video search returns list of video cards HTMLs"""
        response = await async_client.post(url="/search", data={"query": query})
        assert response.status_code == status.HTTP_200_OK

    # @pytest.mark.parametrize("id", [(7501650862555008308)])
    # async def test_single_video_scraping(self, scraper: BaseScraper, id: int) -> None:
    #     """Single video scraping returns HTML <video> tag"""
    #     async with scraper as s:
    #         result = await s.get_video(id=id)
    #         assert "src" in result, "no `src` tag in parsed result"
