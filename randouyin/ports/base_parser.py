from abc import ABC, abstractmethod


class BaseParser(ABC):
    """Class for parsing HTML, returned from Douyin"""

    @abstractmethod
    def get_video_ids(self, page_html: str) -> list[str]:
        """Get video IDs from list video page"""
        ...
