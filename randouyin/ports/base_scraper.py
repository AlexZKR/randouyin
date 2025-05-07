from abc import ABC, abstractmethod
from typing import Self


class BaseScraper(ABC):
    """Class for scraping Doyuin website for videos"""

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb): ...

    @abstractmethod
    async def search_videos(self, query: str) -> list[str]:
        """Scrape Douyin search page for video ids

        Args:
            query (str): query string to search Douyin

        Returns:
            list[str]: List of video ids
        """
        ...
