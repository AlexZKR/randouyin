import logging

import pytest
from randouyin.config.settings import get_settings
from randouyin.ports.base_client import BaseClient

logger = logging.getLogger("test")


@pytest.mark.asyncio
class TestHttpxRequests:
    @pytest.mark.parametrize("query, expectation", [("童笑", "")])
    async def test_video_list_page(
        self, client: BaseClient, query: str, expectation: str
    ) -> None:
        url = get_settings().parsing.douyin_video_list_url.format(query=query)
        result = await client.get_list_video_page(query=url)
        assert result == expectation, (
            f"Received video page didn't match the expectation\n{expectation}"
        )
