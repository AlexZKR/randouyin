from abc import ABC, abstractmethod


class BaseClient(ABC):
    """Client to make async requests to Douyin for HTML and video"""

    @abstractmethod
    async def get_list_video_page(self, query: str) -> str:
        """Get list video page by query"""
        ...
