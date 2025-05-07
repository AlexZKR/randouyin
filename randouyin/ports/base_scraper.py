from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Class for scraping Doyuin website for videos"""

    @abstractmethod
    def search_videos(self, query: str) -> list[str]:
        """Scrape Douyin search page for video ids

        Args:
            query (str): query string to search Douyin

        Returns:
            list[str]: List of video ids
        """
        ...
